---
type: prototype
title: "Audit agent"
description: "Spike for the audit agent: extract checkable claims from the .okf/ bundle, tie each to code, check universal claims, detect drift and write a report."
tags: [prototype]
generated:
  by: process:kmctl/0.12.1
  at: 2026-11-05T18:36:01Z
verified:
  - by: human:jasper
    at: 2026-11-27T20:41:27Z
---

# Audit agent

## Question

Can an agent turn each `.okf/` page into claims that cover it, tie each
claim to code where it can, notice when the code drifts from the claim, and
report all that so a person, or an agent, can review it? It has to work on
any repository with a bundle, not only kmctl.

The hard part is mapping docs to code. OKF docs are append-only, but the
code can change at any moment, so any mapping may stop being correct. Line
numbers should therefore always be avoided; symbols are better.

## Method

`notebook.ipynb`, on the kmctl kernel (the repository's `.venv`). Its
first cell installs what it needs with `uv pip install magika langchain-core langchain-openai langchain-text-splitters tree-sitter-language-pack python-frontmatter pydantic langgraph ast-grep-cli`;
a later `uv sync` removes them again. The LLM cells need
`BIFROST_CC_VIRTUAL_KEY`, which also reaches Clef (`ollama/clef:27b`, a
decision model) through Bifrost's `/v1/decisions`; the HCL cells need
`HCL_SAMPLE_PATH`.
`AUDIT_ROOT` points the notebook at another repository and `AUDIT_SAMPLE`
limits it to that many sampled concepts; the gold-set and drift cells are
kmctl's and must be skipped there.

Labels and scores: `judge_labels.json` is the judged set. `labels/` holds
the other Opus labels (`rand*_out_*` are the random samples; `prec_out_*` and
`neg_out_*` are drawn from single statuses, so they are biased).
`scripts/score_labels.py <ties.json>` scores a run against all of them.
`scripts/partly_newer.py` counts drift among partly claims whose code
changed. Two runs are kept under `results/ties/kmctl/`: the final run
(`final-2026-11-08.json`) and run 22 (`r22-flash-reviewer.json`).

1. List files with `git ls-files`, so git's ignores apply, minus excluded
   folders and limited to chosen extensions.
2. Detect each file's language with Magika and parse it with tree-sitter.
3. Split each `.okf/` concept by its headers, skipping `index.md`,
   `log.md` and deprecated concepts.
4. Send each chunk to an LLM that returns claims as JSON: the claim, its
   evidence, a type (`point`, `structural`, `subjective`) and its links.

What the tool's config file needs is [config](config.md).

## Results

Run on 2026-11-05 with `gemini/gemini-3.5-flash-lite` at temperature 0 on the 26 gold chunks (219 sentences: 146 must be cited, 29
may be, 44 must not be). Scores are per sentence, so they do not depend on
how finely a model splits claims (the `Scorer` cells say how each is counted).

| Variant | Recall | Precision | Type ok | Checkable precision | Claims | Tokens in / out |
|---|---|---|---|---|---|---|
| v0: the notebook's prompt, quotes as evidence | 82.2 | 92.3 | 68.9 | 88.9 | 138 | 16,988 / 17,955 |
| v1: new prompt, cited sentence numbers | 58.2 | 96.9 | 77.4 | 90.1 | 113 | 34,600 / 8,898 |
| v2: a verdict for every sentence | 94.5 | 97.5 | 83.5 | 94.2 | 252 | 32,520 / 13,769 |

- Runs differ even at temperature 0. An earlier run of the same v0 and v1
  prompts, whose cache entries predate the prompt hash and were set aside,
  scored recall 87.7 (v0) and 47.9 (v1): 5 to 10 points from the rows above.
  v2 has one run so far, so its spread is unknown.
- Citing sentence numbers instead of quotes cuts output tokens by about half
  (v1) and leaves nothing to check against the text but a number in range.
  v0's quotes failed to match the text for 10 of its 138 claims.
- v1 stops early: it splits the first sentence into several claims and
  skips the rest of the section. Its prompt also said to list only claims
  someone could check, which dropped the subjective ones.
- A verdict per sentence (v2) makes the model cover every sentence: recall
  goes from 58 to 95 with precision still at 97.5.
- v2's type errors are mostly point against structural (16 of 24); v0's
  first run called 22 point sentences structural.

### The audit graph

One LangGraph graph does the whole audit:

1. `extract` runs once per chunk. Each claim it returns carries a
   quantifier: `exists` means one place settles it, `all` means every
   instance must comply, and `none` means no instance may exist.
2. One branch runs per claim. `lookup` ties the claim without a model, and
   then one of three things happens:
   - an `all` or `none` claim goes to the universal graph;
   - a claim tied only through context, or not tied at all, goes to the
     triage graph;
   - a claim the sentence itself ties is done.
3. The **triage graph** works on one claim at a time:
   - The tracer gets a repo map ranked for the claim: folders, then the files
     that share words with it and what they define. It uses tree-sitter
     tools until it reports where the claim lives, with quotes.
   - Code checks each location and quote. If a quote is not in the file, the
     tracer is told why and tries once more.
   - An adversarial reviewer sees only the claim and the code at each
     location, and tries to reject it.
4. The **universal graph** checks every instance:
   - The model writes broad searches to learn how this repository does the
     thing. From the hits, it writes searches for every instance and says
     what complying looks like.
   - Code collects every instance. Tests and docs are left out unless the
     claim names them.
   - Up to 30 instances: the model checks them in batches of 10, run in
     parallel with `Send`, and sees the whole block each one opens.
   - More than 30: the model writes an ast-grep rule pair, one rule for every
     instance and one for the instances that break the claim. A rule that
     will not parse, matches nothing, or disagrees with a checked sample of
     what it flags and lets through goes back to the model, at most 3 times.
5. The result is one tie record per claim, written to
   `results/ties/<repo>/<commit>.json`, and one Markdown page per concept in
   `~/.cache/audit-agent/report/<repo>/`. Each page shows coverage, the claims to look at
   first, and every sentence with its claims, status and evidence.
6. A rechecker repeats the saved checks without a model:
   - a lookup tie's anchor must still resolve;
   - each of an agent tie's quotes must still be in its file;
   - a universal claim reruns its searches.

Run on 2026-11-06 with `gemini/gemini-3.5-flash-lite` for every model call.

**The quantifier.** The extraction prompt changed, so the gold run redid
extraction. That run scored recall 90.4, precision 96.2, type ok 79.5 and
checkable precision 86.5. This is within the 5 to 10 point spread seen
between runs. The quantifier itself is weak:
- On the 148 gold sentences with checkable claims, the model and the
  labeller agree on "universal or not" for 102.
- The labeller marked 41 sentences universal; the model found 12 of them and
  marked 17 others.
- Reading the 46 disagreements, the labeller is wrong about as often as the
  model. For example, it gave "never edit `.okf/`" one place, while the
  model put "nothing goes to PyPI" right.
- The line between "one place settles it" and "every instance" is fuzzy for
  both readers.

**Where the 894 checkable claims in kmctl's bundle end up**:

| Result | Claims | Share |
|---|---|---|
| Tied by an anchor in the sentence (lookup, no model) | 394 | 44.1% |
| Found or partly, confirmed by the reviewer | 180 | 20.1% |
| Universal: holds | 53 | 5.9% |
| Universal: broken | 21 | 2.3% |
| Universal: no instances found, or no working rule | 85 | 9.5% |
| Not found | 68 | 7.6% |
| Unconfirmed (reviewer rejected, only tests or docs, quote not in file) | 86 | 9.6% |
| Not about code | 7 | 0.8% |

**The tracer with a repo map and a quote retry.** These are the 124 claims
the lookup could not tie, run through three versions of the triage graph:

| Version | found | partly | rejected | quote not in file | not_found | tool calls |
|---|---|---|---|---|---|---|
| Plain tracer | 43 | 6 | 14 | 15 | 41 | 6.1 |
| With the repo map | 52 | 8 | 15 | 18 | 22 | 5.2 |
| Map, and one retry on a failed quote | 62 | 12 | 16 | 0 | 29 | 5.6 |

**Ties through context are now checked.** 217 claims were tied only through
the sentence before or the concept's `sources`. The agent confirmed 106 of
them, rejected 55 and found nothing for 39. Half of these ties pointed at the
wrong code or at nothing.

**Universal claims.** Of the 159, 73 were checked per instance and 57 by the
rule route; the searches found nothing for the other 29.
- The rule route worked for 23 of the 57. The other 34 ran out of rounds
  (37 of the 57 used all 3).
- On average a claim took 3.8 model calls.
- The "broken" verdicts mix real findings with scope errors. Three files
  parse front matter with their own `yaml.safe_load` while a decision says
  `okf.py` is the one reader; that one needs a person to judge. But the
  check of "`src/kmctl/__init__.py` only parses, prints and sets exit codes"
  flagged functions in `action/agent.py`. The checker cannot tell which
  instances a claim covers.

**Planted violations.** Seven universal claims were each broken on purpose in
a copy: a PyPI publish step, a removed command put back, a call to APM, a
rule file without `applyTo:`, a flag flipped, a `git push`, an import.
- **The usual route caught 5 at the planted line.**
- It missed:
  - the rule file without `applyTo:`, because instances are lines, so a
    missing line has nothing to match;
  - the `git push`, because the searches looked elsewhere;
  - the restored command, which was flagged, but not at the plant.
- **Forcing the ast-grep route caught 1.** Flash-lite rarely writes a
  working ast-grep rule.
- **Rerunning the saved searches without a model flagged 3 of the 7 as
  changed.**

**Drift, without a model.** Planted drift deleted 15 files and renamed 15
symbols. Every saved tie was then rechecked on that copy:
- **Claims resting on the planted anchors:** 112 drifted, 20 universal ones
  changed, and 34 still hold, because the agent had found them elsewhere.
  42 had nothing to recheck: they were not found, not code, or could not be
  checked.
- **Every other claim:** 65 drifted, and all 65 rest on a deleted file or
  renamed symbol through another anchor or quote, so no tie raised a false
  alarm.
- **83 universal claims count as changed.** A deleted file takes its
  instances with it, so "changed" means "check again", not "broken".
- **On the unchanged repository, every tie still holds.**

**Drift, with the agent.** These are the 63 claims resting on the planted
anchors:

| | Unchanged | Drifted, new claim | Drifted, earlier location given |
|---|---|---|---|
| found or partly | 41 | 10 | 12 |
| not found | 8 | 43 | 43 |
| still found something else | | 5 | 7 |

**A second repository.** The same notebook ran on 15 sampled concepts from
the `.okf/` bundle of localstack, a Nomad and Terraform homelab, with
`AUDIT_ROOT` and `AUDIT_SAMPLE`. It gave 355 checkable claims:
- 135 tied by the lookup, 77 found or partly, 54 not found, 27 unconfirmed;
- of the universal claims, 21 hold, 9 are broken, 20 had no instances and 8
  could not be checked.

The run showed two places where the prototype assumed kmctl:
- The file reader read only kmctl's file types, so `.hcl` and `.tf` were
  invisible. Universal claims about jobspecs found nothing.
- Ties through context sent only 3 claims to the agent.

Both are fixed. The universal checker first saw 6 lines around each
instance, and two false "broken" verdicts came from that: a constraint 15
lines down went unseen. It now sees the whole block.

### Round of 2026-11-07/08: decision models, confirmations, second opinions

**How it is measured now.** Three sets of claims labelled by Opus subagents
with a shell, none checked by a person:
- the 50 judged claims (`judge_labels.json`), sampled from untied claims;
  recall counts the 43 the judges called supported or partly;
- 166 labels drawn from one status each (found, needs a person, warnings),
  so they lean towards the run they came from;
- **60 claims drawn at random from all statuses**, the only unbiased one.

**Can code settle the claim? A decision model.** The checkability step asks
typed yes-or-no questions, so a decision model can answer them: Clef
(through Bifrost's `/v1/decisions`) or Jev (TypeSafe). On 353 claims, at
each model's best setting:

| Model | Checkable kept (34) | Your ten | Gold kept (169) | Answers that change between runs |
|---|---|---|---|---|
| Flash, three runs | 28-29 | 7 | 160-162 | 24 of 353 |
| DeepSeek V4.1 Flash, two runs | 19-23 | 5-8 | 141-143 | 48 of 352 |
| Clef, four questions, cut-off 0.5 | 28-29 | 8 | 166-167 | 2 of 353 |
| Jev, four questions, cut-off 0.6 | 27 | 5 | 168 | 2 of 353 |

Clef is the default. With only the four questions it rarely flags a claim,
and in a full run it held back 3 of 22 not-code claims. Four more questions
(what an outside tool does, a rule for people, a purpose, a measurement no
file records) bring that to 18 of 22, at a cost of 3 of 254 true claims. A
claim flagged broad, vague or unclear is traced anyway and goes to a person
only if the trace does not settle it. Since run 24, a purpose is also traced
first and is not code only if the trace does not settle it; a trace that does not settle it while
Clef leans (above 0.3) towards not code makes it not code.

**Contradicted was wrong every time.** A hand check of the 12 contradicted
claims found no drift: 5 came from text a later part of the page replaces,
7 were misreads. A contradicted or not-found claim now gets two checks:
Clef asks whether a later part of the page replaces the sentence (above
0.9, not code), and Flash reviews the code again and must quote the line
that differs. The same Flash review now checks universal "broken"
verdicts, 7 of 10 of which were wrong.

**Other changes, each measured on a full run:**
- the reviewer needs more than one example for "only" and "the one";
- a claim the extractor left without text takes its sentence;
- a "none" claim whose searches find nothing holds;
- a quote counts when a line is 90% the same, since models drop a closing
  quote or bracket;
- **a second opinion**: a claim the Flash-Lite tracer does not settle is
  traced again by Flash (judged recall 28 and 30 of 43 to 32 and 35);
- a universal claim with nothing to check, or no working search, goes to
  the tracer;
- a test or doc counts as evidence when the claim is about that file;
- when the tracer says something is gone but names nothing, the names come
  from the claim;
- **three extraction runs, merged**: a run skips sentences at random, so a
  sentence one run leaves without a claim takes another's. Gold recall
  went from 84.9 (one run) to 93.8, precision from 93.3 to 91.9;
- **a review of lookup ties**: Flash-Lite reads the code a lookup tie points
  at; a tie that only shares a name goes to the tracer. Letting it answer
  "not code" sent 156 true claims there, so it cannot.

**Where kmctl's claims end up**, before this round and after (run 20):

| | Before | After |
|---|---|---|
| Claims | 1,025 | 1,214 |
| Tied, found, partly or holds | 724 | 943 |
| Not code | 60 | 213 |
| Needs a person | 74 | 12 |
| Warnings (contradicted, broken, not found, unconfirmed, could not check, no instances) | 170 | 46 |
| Contradicted | 12 | 11 |

**On the 60 random claims:** 44 to 46 of 48 true claims are settled
(92-96% over runs 12 to 14, which retrace and so differ by a claim or two),
44 to 46 of the 49 settled claims are true (90-94%), 6 of 10 not-code
claims are held back, and neither of the 2 drifted claims is flagged.

**kmctl's warnings, checked.** An Opus check of the 45 warnings of run 13
found 2 real drifts (both from ADR 0034's "a plain rename, not `git mv`";
`mv.py` now runs `git mv`), 16 false alarms, 11 not code, 9 history and 5
claims extracted wrong. Two changes followed: a claim the trace does not
settle in a context section (Context, Background, Alternatives, Rejected,
Considered options) is not code, and the tracer and reviewer may cite a
document when the claim is about that document ("Supersedes ADR 0010",
"This page points to the indexes"). Run 14 keeps both drifts flagged, has 35
warnings, and 7 of the old false alarms are now found or partly. Across all labels,
most drifted claims are sentences a later part of an ADR replaces, which
the audit now calls not code; the real misses are a hook name that is gone
and a docstring the reviewer took as proof.

**After 03:30: extraction and a stricter view of outside tools.** A second
random sample of 60 (120 in all) put run 15 at retrieval 85 of 93, precision
85 of 99, 9 of 19 not-code claims held back and 1 of 8 drifted claims
flagged: worse than the first 60 suggested. Then:
- **Flash fills extraction gaps**: Flash-Lite twice, then Flash for the
  sentences both left without a claim; gold recall 98.6 (Flash alone: 89.0
  at precision 100). Flash first scores the same but rewords every claim.
- **The extractor keeps conditions, tense and negation**: labellers found
  claims that dropped an "if", restated the past in the present, or turned
  a rejected option into a claim. With the new rule one run's gold recall
  went from 84.9 to 92.5 and precision from 93.3 to 95.6; the merged runs
  from 98.6 / 92.7 to 95.2 / 95.3.
- a lookup tie the review calls partly goes to the tracer (it caught a hook
  name that is gone);
- **a settled claim Clef thinks is about an outside tool** (above 0.3) is
  not code: on labelled settled claims that caught 6 of 8 not-code ones and
  3 of 103 true ones;
- an extra extraction run that times out no longer stops the audit.
- **a hint, without a model**: a settled claim whose cited code changed (git
  blame) after its sentence was last edited is marked in the report, with a
  list per page. On labelled settled claims it marks both drifted ones and
  17 of 77 true ones, so it is a pointer for a person, not a status; it marks
  230 of kmctl's 943 settled claims.
- **Tried and dropped**: a Flash drift review of every found or partly
  claim turned 18 into contradicted, and an Opus check found none was drift
  (13 history, 6 hold, 3 misread). Jev and Clef averaged separate not-code
  claims barely better than Clef alone.

**On 120 claims drawn at random from the final run** (two samples of 60,
labelled after the changes): 83 of 89 true claims settled (93%), 83 of 89
settled claims true (93%), 15 of 16 not-code claims held back (94%), and 3
of 15 drifted claims flagged. Six of those 15 are ADR sentences a later
correction on the same page replaces, and one restates the past; the audit
calls those not code on purpose, since an ADR is append-only and corrected
below. Without them it flags 3 of 8: the rest read as found or partly (a
count that went from five to six, a job condition that changed).

**Tried and dropped after the final run:**
- **Flash as reviewer, Flash-Lite as tracer** (`all-lite-flashrev-2nd`): on the 120 random claims, 81 of 89 settled and 81 of 84 settled claims true, with drift unchanged at 3 of 15. Judged recall fell from 32-33 to 26-27 of 43, because the stricter reviewer rejects ties the judges accept.
- **A different cut-off for the outside rule:** on the 18 labelled claims the rule overrides, it is right on 11. Moving the cut-off to 0.4 or 0.5 trades true claims for not-code claims about one for one.
- **Kept: partly claims with newer code join "Look at first".** A claim the audit marks partly, whose cited code changed after its sentence, is drift in 5 of 12 distinct labelled claims across the final run and run 22. Four of the five come from the random samples. Among the other settled claims, 7 of 223 are drift (3%). Not-code labels are left out, and a claim labelled in both runs counts once. `python3 scripts/partly_newer.py results/ties/kmctl/final-2026-11-08.json results/ties/kmctl/r22-flash-reviewer.json` gives these counts. Making it a status would cost true claims, so the report lists these claims with the warnings at the top of each page and leaves their status as it is. Retrieval and precision do not change. That is 15 to 29 kmctl claims per run.
- **Dropping the outside rule** on the random samples of both repositories (191 true and 30 not-code labels) would settle 5 more true claims and let 7 more not-code ones through. The rule stays.
- **Clef's outside question with the cited code in front of it** (`scripts/outside_with_code.py`, the 21 labelled claims the rule overrode): no separation. True and not-code claims both score from 0.03 to 0.93.
- **Stale labels understate the audit.** The extractor now keeps tense and conditions, so 32 judged labels (29 distinct claims) were scored against a reworded claim. `scripts/stale_judged.py` pairs each with the current claim, and Opus labelled the current wording (`labels/judged_relabel.json`). On those claims the final run's scores go from:
  - settled true claims: 18/24 to 19/22;
  - settled claims that are true: 18/19 to 19/19;
  - not-code held back: 3/4 to 6/6;
  - drift flagged: 0/1 to 1/2.

  Several old "misses" are past-tense history the old label judged in the present. `score_labels.py` now prefers the fresh labels.

  The other 127 labels on reworded claims (`scripts/stale_labels.py`, `labels/stale_relabel_*.json`) changed little. Settled-claim precision went from 85/94 to 86/94, and not-code held back from 13/20 to 15/18.

  With all fresh labels, the final run (before run 24) scores:
  - retrieval 225/255 (88%);
  - precision 225/241 (93%);
  - not-code held back 38/44 (86%);
  - random 120: 84/91, 84/89, 14/15, drift 3/14.

  Of the claims sent to not code, each rule holds back more not-code claims than true ones:
  - outside: 12 to 7;
  - rule: 6 to 3;
  - history: 4 to 2;
  - context section: 6 to 0.

  **Kept: purpose claims are traced first** (run 24). Before, a claim Clef called a purpose stopped early as not code, which caught 2 true claims and 1 not-code claim. Now the tracer sees it. If the trace doesn't settle it, the leaning rule still makes it not code. Of kmctl's 8 such claims, 7 are now found, several of them plain code facts with a reason attached ("A missing verified does not make a docs page due"). All labels: retrieval 227/255, precision 227/244, not-code held back 37/44. These are the current pipeline's numbers. Random 120 is unchanged. When the checker gives no probabilities (the Flash path), an unsettled purpose claim is still not code.

  **A switch for superseded text** (run 26, `AUDIT_SUPERSEDED_WARNS=1`, off by default). The claim gets status `superseded`, listed under "Look at first", and is not marked not code. The results:
  - drift flagged on the random 120 goes from 3/14 to 9/14;
  - retrieval stays at 227/255;
  - not-code held back goes from 37/44 to 36/44;
  - kmctl gets 42 more warnings.

  `scripts/superseded_as_drift.py` gives the same numbers offline. The run is kept as `results/ties/kmctl/r26-superseded-warns.json`. A lower cut-off for the superseded question (`AUDIT_SUPERSEDED_CUTOFF=0.7`, run 30) marks 45 claims instead of 42 and changes no score, so it stays at 0.9. Counting the partly claims with newer code that the report also lists at the top, a reader sees 4 of the 14 random drifts at the top of a page by default, and 10 of 14 with the switch on. On localstack the switch marks one claim (the removed MinIO provider's old description) and changes neither labelled drift.

  **The kept runs, scored the same way** (`scripts/score_labels.py`, all 408 labels with the refreshed ones):

  | Run | True claims settled | Settled that are true | Not-code held back | Random 120 drift flagged |
  |---|---|---|---|---|
  | final (05:39) | 225/255 (88%) | 225/241 (93%) | 38/44 (86%) | 3/14 |
  | run 22, Flash reviewer | 213/255 (84%) | 213/221 (96%) | 41/44 (93%) | 2/14 |
  | run 24, purpose traced (default now) | 227/255 (89%) | 227/244 (93%) | 37/44 (84%) | 3/14 |
  | run 26, superseded as warning | 227/255 (89%) | 227/244 (93%) | 36/44 (82%) | 9/14 |
| run 28, Flash reviewer and superseded as warning | 214/255 (84%) | 214/223 (96%) | 39/44 (89%) | 9/14 |

  Settling a claim only when both run 24 and run 22 settle it gives 211/255 (83%), precision 211/218 (97%) and 42/44 not-code kept out of the settled claims (offline, on the saved runs). Settling it when either run does adds 2 true claims and 6 wrong ones. With the superseded switch on in both (runs 26 and 28), the random 120 gives settled 81/91, precision 81/83 (98%), and 12 of 14 drifted claims left unsettled and not held back, so they reach the reader. That is the strongest drift setting tested. On the older random sample of 83, whose drifts are not superseded text, it does less: drift goes from 1/4 to 2/4, while settled true claims drop from 62/71 to 57/71. It costs a second triage run per claim (the Flash reviewer), about an hour on kmctl.

  The Flash reviewer trades 14 true claims for 3 more not-code ones held back and higher precision, so it suits a reader who wants fewer wrong "found" verdicts over coverage.

  Superseded ADR text is the exception: 6 drifted, 2 true, 1 not code. Whether text a later correction replaces should count as drift is a design choice, not a tuning one.
- **The drifted claims still read as found** are borderline. One is a file the code writes in the consumer's repository, one matches the code, and one depends on how you count install lines.

The first of those two samples, alone (run 20):
44 of 46 true claims settled (96%), 44 of 45 settled claims true (98%), all
9 not-code claims held back, 2 of 5 drifted claims flagged. On the 88 of the
earlier 120 that still match a claim: 66 of 74 (89%) and 66 of 69 (96%).
Across all 269 labels that match: retrieval 190 of 215, precision 190 of
202. A second full run with fresh traces (the same extraction and
checkability) gave 44 of 46 and 44 of 47 on that sample, 8 of 9 not-code
claims and 1 of 5 drifts, and 939 settled claims against 943: two runs differ
by a claim or two in each count. Drift is the weak spot: a claim that only partly holds, or holds in
the tracked files but not the working tree, still reads as settled.

**Planted drift, rerun with the new tracer.** On the copy with deleted files
and renamed symbols, the 61 claims resting on them:
- original repository: 59 found, 2 partly (the old tracer found 41);
- drifted: 23 not found, 4 only tests or docs, 2 or 4 found at the renamed
  symbol, and 15 to 17 found elsewhere. The stronger tracer finds a second
  place for more claims than the old one (5 to 7). Some are real (a field
  list kept in two modules), and a quote that is only a docstring or comment
  no longer counts as evidence, which changed none of them;
- the recheck without a model flags 156 planted ties as drifted and 159
  others that rest on a deleted file or renamed symbol, as before.

**Planted violations of universal claims** (the test now finds a planted
claim by its closest text, since extraction rewords claims): caught at the
plant for 3 of 7 ("Nothing goes to PyPI", "`kmctl plugin patch` never runs
APM" with the rule forced, "action/agent.py does not import kmctl"); one
plant matched the wrong claim. The universal checker did not change this
round. On Flash (`universal_runner_for(..., model=FLASH)`) it caught 4 of 7
at the plant but called one unchanged claim broken; seven plants cannot
tell the two apart, so Flash-Lite stays.

**localstack**, with every change (run of 2026-11-08 02:17): 422 claims,
293 settled (90% of the 325 code can check), 28 warnings (6.6%), against
about a third before, and both real drifts flagged as contradicted. With the
later extraction and outside-tool changes (05:20): 467 claims, 333 settled
(88% of the 377 code can check), 36 warnings (7.7%). On 40 of its claims drawn
at random and labelled by Opus: 28 of 32 true claims settled (88%), 28 of
29 settled claims true (97%), 3 of 4 not-code claims held back, 0 of 2
drifts flagged. The outside-tool cut-off costs more here: two of its three
sampled hits are claims the repository's own config settles (an image tag,
a firewall as the only access control for NATS). An Opus
check of its 34 not-found and contradicted claims, before the last change,
found 2 real drifts (both contradicted: a dashboard that keeps its last
payload, justfile recipes that no longer set a token prefix) and 24
sentences from removed spikes and plans, 19 of them on one draft proposal.
So a claim the trace does not settle on a page that describes a plan (OKF
type proposal, or status draft, proposed, rejected or superseded) is now
not code: not built, rather than drift. That took localstack from 49
warnings to 28 and left kmctl as it was.

## Conclusion

The pipeline works end to end on two repositories and writes a report a
person can act on. It does the four jobs unevenly:

- **Claims and coverage: good.** A verdict per sentence covers the page, and
  each page in the report says how many sentences hold a claim. The
  quantifier that routes a claim (one place, every instance, none) is
  unreliable for model and labeller alike.
- **Tying: good.** On 120 random claims from the final run, 92% of the true
  ones are settled and 94% of the settled ones are true (84/91, 84/89, with
  refreshed labels). Over all 408 labels: 227 of 255 true claims settled
  (89%), 227 of 244 settled claims true (93%). A lookup tie is now read by a
  reviewer, and a claim the first tracer misses gets a second, on Flash.
- **Universal claims: weak.** Per instance it caught 5 of 7 planted
  violations. It cannot see a missing file or line, it does not know which
  instances a claim covers, and flash-lite rarely writes a working ast-grep
  rule.
- **Drift: good for removed code.** Rechecking saved ties needs no model,
  flagged every planted removal, and raised no false alarm. It does not see
  code that keeps its name but changes behaviour; only rerunning the
  reviewer on each tie would catch that.

- **Can code settle it: good.** 14 of 15 random not-code claims are held
  back (37 of 44 over all labels), after an "outside tool" cut-off on
  settled claims. A purpose is traced first, since it often carries a fact.
- **Drift in the text: weak.** 3 of 14 random drifted claims are flagged.
  Most of the rest are ADR text a later correction replaces, which the audit
  calls not code by design. A claim that only partly holds still reads as
  settled, but if its code changed after the sentence, the report lists it
  with the warnings at the top of the page (drift in 5 of 12 such labelled
  claims).

Next: catch drift that keeps names (a docstring is not proof; a hook name
that is gone). Have a person check the labels: they come from Opus, and 159 had to be
redone when the extractor's wording changed. Decide whether superseded ADR
text should count as drift. Give universal checks the instance's scope, and let
instances be files as well as lines. Try a stronger model for the rule
writer and tracer. Have a person check the gold labels, including the
quantifiers.

## Files

All code is in `notebook.ipynb`; running it top to bottom rewrites the data
files below. Model calls are cached per chunk by content key, model and
prompt hash in `results/cache/`, so a rerun only calls the model for chunks
that changed.

- `chunks.jsonl`: every chunk, with stable id, numbered sentences and key.
- `gold_ids.txt`: the seeded, stratified sample of gold chunks.
- `gold.jsonl`: the hand labels, with the key each chunk had when labelled.
  Set `WRITE_GOLD` in the notebook to rewrite it after relabelling.
- `results/*.jsonl`: the gold-set extraction, one file per model.
- `gold_quantifiers.json`: the quantifier labels of the gold sentences that
  hold a checkable claim, by a subagent; no person has checked them.
- `results/triage/` and `results/universal/`: the triage and universal
  graphs' results, cached per claim, prompts, variant and repository copy.
- `results/ties/<repo>/<commit>.json`: one tie record per checkable claim,
  for an agent and for the rechecker. `final-2026-11-08.json`,
  `r22-flash-reviewer.json` and `r24-purpose-traced.json` are kept runs
  the README's numbers come from.
- `labels/` and `scripts/`: the Opus labels and the scripts that score a
  run against them (see Method).
- The report, one page per concept and an index, goes to
  `~/.cache/audit-agent/report/<repo>/` (or `AUDIT_REPORT_DIR`), outside the
  bundle, because OKF validation would read its pages as concepts.
