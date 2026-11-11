---
type: prototype
title: "Audit CLI"
description: "The audit agent's claim extraction as a Typer CLI: audit claims extract or diff a bundle or one concept file, into a per-project SQLite database, set by audit.toml."
tags: [prototype]
generated:
  by: claude-opus/5.5
  at: 2026-11-08T12:00:00Z
---

# Audit CLI

The `prototypes/audit-agent` notebook, up to and including claim extraction,
as a command-line tool. It cuts an `.okf/` bundle (or one concept file)
into sections and extracts claims with the notebook's prompt. By default
each section gets two runs of one model; the second adds claims for the
sentences the first skipped. (The notebook added a third run on a stronger
model and reached gold recall 98.6; that run is left out for now, and
`claims.runs` can add it back.) Everything goes into one SQLite database per
project.

`audit init` writes a generic `audit.toml`: OpenAI's endpoint, keyed by
`OPENAI_API_KEY`, and no model. Both verbs refuse until
`agents.extractor.model` is set.

## Use

```bash
audit claims diff .                      # what is extracted, what changed, how many model calls
audit claims extract .                   # extract the bundle (a repository with .okf/, or the bundle folder)
audit claims extract .okf/manifesto.md   # or one concept file
audit claims list                        # documents and claim counts in the database
audit claims list .okf/manifesto.md      # one document's claims, with the model's reasons
audit init                               # write audit.toml with every setting
```

Run it with `uv run --project .okf/prototypes/audit-cli audit ...`.

- `claims extract PATH` cuts each live concept into sections and runs each
  section through `claims.runs`, with a progress bar on stderr. A run
  already stored for a section's current text is read, not called again.
- `claims diff PATH` compares the text with the database, per concept and
  section: up to date, new, changed (with sentences added and removed),
  incomplete (a run is missing) or removed. It counts the model calls
  `extract` would make, writes nothing and needs no key.
- `claims list [PATH]` shows the documents the database holds, with sections
  and claims per kind; for one file, or with `--claims`, each claim with its
  sentence, kind and reason. `--kind` filters. It reads only.
- All three take `-c audit.toml`, `--json` and `--debug`. Exit 0 means done or up
  to date; 1 means a section failed (extract) or extraction would change
  claims (diff); 2 means the path, settings or key are wrong.

## Settings

`audit.toml` holds every setting; `audit init` writes one with comments.
A misspelt key is an error.

- `[files]`, for the code-reading stages still to come (claims ignore it):
  `include_extensions`, `exclude_dirs`, `exclude_patterns`,
  with `extend_` lists that add to the defaults. Git decides first, so an
  ignored file is never read.
- `[providers.NAME]`: an OpenAI-compatible `base_url` and the environment
  variable that holds its key (a `.env` file works too).
- `[agents.NAME]`: a provider, model, temperature, timeout and retries.
- `[claims] runs`: agent names in order, `agent@salt` for a second run of
  the same agent. The first run's claims stand; each later run adds claims
  for sentences the earlier runs skipped.
- `[concurrency] max_model_calls`: one bound on calls in flight, shared by
  every run (default 12).
- `[logging]`: `level` (info by default) and an optional fixed `path`.
  Each run appends JSON lines to `<user log dir>/audit-cli/<project key>.log`
  (on macOS `~/Library/Logs/audit-cli/`): what was asked, the settings
  file, the plan (model calls versus stored results), one line per section
  (claims per run, calls, tokens, seconds), warnings and a summary.
  `--debug` adds each model call and answer.
- `[telemetry] enabled`: true (the default) or false; it sets
  `LANGSMITH_TRACING`. Everything else is LangSmith's own environment
  variables, in your shell or a `.env` file: `LANGSMITH_API_KEY`, and
  `LANGSMITH_PROJECT` or `LANGSMITH_AGENT_ID` with
  `LANGSMITH_AGENT_ENVIRONMENT`.
- `[database]`: see below.

## The database

The database sits in the user's data folder (`platformdirs`), one folder
per project: `<data dir>/audit-cli/projects/<key>/audit.sqlite`, on macOS
under `~/Library/Application Support`. The key is the repository's folder
name plus a hash of its full path, so two checkouts never share one.
`database.project_key` names the folder instead, and `database.path` picks
a fixed file. `AUDIT_CLI_DATA_DIR` moves the data folder.

It is not only for claims. Each stage owns its tables, and the schema grows
by Alembic revisions in `src/audit_cli/migrations/versions/` (0001: the
first tables; 0002: verdict reasons). Opening a database upgrades it to the
newest revision on the same connection, and `alembic_version` records where
it stands. A new stage adds a revision. Queries stay plain `sqlite3`. Today
it holds `project`,
`files`, `chunks`, `claim_extractions` (the claims stage's cache: one row per
chunk text, model, prompt and salt), `sentence_verdicts` (every sentence's kind and reason) and `claims` (the merged claims, with
the notebook's `claim_id`). A second pass over unchanged chunks reads
`claim_extractions` and calls no model. The cache key covers everything the
model sees, the concept id, title and status included, so a renamed concept
is extracted again. An answer the model gave in a form that could not be
read is not stored: the command exits 1 and the next pass asks again. So
is an answer that still leaves a sentence without a verdict after the model
is asked a second time for the skipped ones; a stored answer with such a gap
counts as not made. A verdict of kind none is an answer, so a section with
no claims is fine. A
chunk whose text changed loses its old claims until it is extracted again.

## Results

On kmctl (2026-11-08): 156 sections from 31 concepts, as the notebook
found. `extract .okf/manifesto.md` took 18 calls for 77 claims and
`extract .okf/summary.md` 12 calls for 43 claims; `diff` then reported both
up to date and 450 calls left for the rest of the bundle. Earlier, before
the CLI was cut down to claims: Three manifesto chunks took 9 run results and 43 claims
(16,911 tokens in, 13,250 out); a second pass read all 9 from the database.
After the review fixes a fresh database gave 49 claims from the same three
chunks (9,304 tokens out): the model's answers vary between runs, which is
why runs are merged. Those runs included the Flash fill that is now left out.

## Reasons and examples, scored on the gold set

The prompt asks for a one-sentence `reason` per verdict, stored with each
claim and, in `sentence_verdicts`, for sentences with no claim. It also
gives each kind an example of what it is and near misses that are another
kind. `scripts/gold_compare.py` scores five prompts on the notebook's 26 gold
chunks with Flash-Lite, two runs each, merged as `extract` merges them
(results in `results/gold_compare.json`; the old prompt's runs are the
notebook's cache):

| Prompt | Recall @1 / @2 | Recall merged | Precision merged | Output tokens |
|---|---|---|---|---|
| old (the notebook's) | 92.5 / 91.1 | **95.2** | 95.3 | 34,470 |
| reason only | 89.0 / 88.4 | 92.5 | 93.9 | 40,833 |
| reason and examples (the CLI's) | 89.0 / 90.4 | 93.8 | 93.6 | 41,699 |
| reason after the claims, with examples | 91.1 / 88.4 | 93.8 | 92.9 | 41,683 |
| examples only | 70.5 / 81.5 | 83.6 | 96.5 | 28,618 |

Every change lowered recall. The reason costs 1.4 to 2.7 points merged and
a fifth more output, wherever it sits; the examples help only together
with it, and alone they cut recall by 12 points (one sample each, so a
difference of a point or two may be noise). The CLI ships the reason with
the examples, the best of the variants that explain their kinds.

### On DeepSeek (the model the CLI now runs)

The same five prompts on `ollama/deepseek-v4.1-flash`, every one run fresh
(`results/gold/ollama_deepseek-v4.1-flash/`):

| Prompt | Recall @1 / @2 | Recall merged | Precision merged | Checkable precision | Output tokens |
|---|---|---|---|---|---|
| old (the notebook's) | 71.2 / 87.0 | 92.5 | 93.1 | 89.0 | 542k |
| reason only | 93.8 / 94.5 | 96.6 | 95.4 | 92.4 | 649k |
| reason and examples (the CLI's) | 78.1 / 94.5 | **99.3** | 95.5 | 93.2 | 718k |
| reason after the claims, with examples | 95.2 / 83.6 | 98.6 | 93.8 | 91.8 | 753k |
| examples only | 92.5 / 90.4 | 95.9 | 93.7 | 93.6 | 584k |

On DeepSeek the result turns around: every prompt with a reason beats the
old one, and the CLI's prompt is best (99.3 recall merged). Single runs
swing by up to 16 points, so the second run carries a lot and one sample
per prompt is thin. Output is mostly the model's thinking: about 14k tokens
per call.

The low single runs are mostly not misses. In 20 of the 260 saved answers
the model returned no verdict at all, twice, and the script scored those
sections as all missed: in the CLI's run 1, three sections held 28 of the
146 sentences to catch, and on the other 23 it caught 114 of 118 (96.6).
The CLI now counts such an answer as failed rather than storing a section
with no claims; `scripts/gold_gaps.py` lists them, and `gold_compare.py`
asks for them again on its next run.

## Settling claims without a model (pilot)

`scripts/settle_claims.py` takes the 187 claims stored from three
decisions (0017, 0023, 0035) and tries to settle them from the repository
alone: git (tracked files and history), the repository's CLIs (Typer
`--help` panels, argparse read from source, with flags and defaults) and
tree-sitter definitions. Markdown, `.okf/` and `.loop/` (spike copies of
scripts) are never searched. Results are in `results/settle/`.

- **Settled: 8 of 187 (4%), all correct** by hand: five "no longer
  exists", one flag default, one "no import of", one "has a tool".
  Ten deliberately wrong claims, built from these, all got the right verdict.
- **Every anchor located: 125 of the 135 claims that name something.** A
  checker can start at those files instead of searching.
- **An anchor missing: 10, none of them drift.** They are placeholders
  (`agent-report-NAME`), patterns (`priority/*`), a system path
  (`/proc/PID/environ`) and names that only tests hold.

Few claims settle because most say what code does, not that it exists.
Many could still be checked without a model (every `setup-uv` step sets
`enable-cache: false`), but turning the sentence into that query needs a
model. Two first-pass mistakes are worth keeping: a name found only in tests
is often a test that it stays gone, and a `/` does not make a path (slash
commands, action refs, labels).

## Claims turned into checks (pilot)

A model writes each claim's check once; the check then runs on every audit
with no model. A check is data, not code: steps from a fixed list (a file
exists, a regex matches in a glob of files, a JMESPath query over YAML,
TOML or JSON, a Python definition or import, a repository CLI's `--help`),
over tracked files only, never markdown or `.okf/`
(`src/audit_cli/checks/steps.py`). The writer is an agent with read,
search and try-check tools (`src/audit_cli/checks/writer.py`):

- Old tool output is trimmed. The newest results, up to about 6k tokens,
  go in full; older ones, and older copies of a repeated call, become a
  one-line note. A note is never longer than what it replaces.
- Each batch has its own budget (20 turns, 250k tokens): a warning two
  turns before the end, and a last call that can only return a submission.
- A submitted check that fails goes back once with what it saw: fix it, or
  keep it marked `drift:`.

`scripts/compile_checks.py write` ran three batches, 19 claims, on DeepSeek
with `reasoning_effort=low` (`scripts/probe/thinking.py`: low cut output on
a small prompt from 594 to 229 tokens). Results are in `results/checks/`.

| | |
|---|---|
| Claims | 19: 16 checks (6 exact, 10 proxy), 3 with a reason no check fits |
| Tokens | 438k in, 23k out: about 23k in per claim |
| Rerun of the saved checks | 0.0 s, no model |
| Graded by hand | 10 good, 2 fair, 3 weak (a word's absence, `asyncio.run` exists for "one run", guessed test names), 1 wrong |

The wrong one is a false drift alarm: it greps the whole audit workflow for
`GH_TOKEN`, which the publish job holds by design. It was handed in at the
last turn, so it never went back.

What the trials taught:

- DeepSeek through Bifrost ignores a forced tool choice and calls tools it
  was not given. Only structured output at the last call made a batch
  hand in at all; before that, three trial batches ended with nothing.
- It saves every submission for the end, whatever the prompt and the
  reminders say, so a batch uses its whole turn budget. A batch of 3 took
  8 turns (15k tokens a claim); batches of 8 took 19 to 20 (24k a claim).
- Trimming saved 13% of the history sent in the one batch measured
  (383k of 440k characters). Trimming only the newest three results made it
  re-read the same files: it read one workflow four times.
- The four "no longer exists" claims `settle_claims.py` settles for free
  cost model turns here, so settling goes first.

## Cost pilots, each measured (2026-11-10)

Scripts in `scripts/pilots/`, results in `results/pilots/`. Spend: 411k
DeepSeek tokens of an agreed 500k cap (`spend.json`); every call is traced
in LangSmith (`kmctl-local`). The paid pilots ran on two samples: the 19
claims the check-writing agent was graded on, and a fixed random 30 of the
113 claims the settle step found lines for (17 of the 19 have none).

| Idea | Result |
|---|---|
| Settle with no model | 8 of 187 settled, all right (above) |
| Agent writes checks (baseline) | 23k tokens a claim; 10 of 16 checks good |
| One call per claim, found lines shown | 5.8k tokens a claim (30 with lines): 11 hold, 6 fail, 7 reasons, 6 unreadable; on the 19 without lines, 3.1k and mostly "nothing shown" |
| One call per shared file | **2.5k tokens a claim: 17 hold, 5 fail, 4 reasons, 4 unanswered** |
| Default thinking vs low | 10.3k tokens a claim on 10; 7 of 10 answered in prose, not the form. Low stays |
| Prompt caching | Works through Bifrost: 84% of input cached one call per claim, 39% grouped |
| Batch pricing | Not offered: Bifrost has no batch key for its ollama provider |
| Same fact in two places | Clef 2 of 187, Jev 1 of 187, of 111 candidate pairs; across a whole bundle untested |
| Leave out what code cannot settle | The extractor's kinds: 7 of 187. The router's "not current": 23, of which about 7 were code facts |
| Re-check only what changed | 125 claims tied to files; over 60 commits a commit sends back 14 (median, 11%), 24 send back none; 62 claims tie to nothing and need another trigger |
| Keep checks, run them later | Over 1,000 commits none of 16 flip; before the audit script existed 13 do, as they should |
| Decision model as router (Clef) | 187 claims in 67 s. "When" is right for 14 of the 23 it routes away; "can code answer" is noisy; its kind agrees with the extractor 63%. **"Enough information" predicts the one call: 13 of 14 answered "enough" claims got a check that holds, 4 of 8 "not enough"** |
| The same router on Jev | 187 claims in 15 s, 486 calls in all (about $0.05). "Enough" sorts as well as Clef's: 13 of 15 answered "enough" hold, 4 of 7 "not enough". "Can code answer" says yes to 182 of 187, so it sorts nothing; kind agrees with the extractor 70% |

Both one-call runs caught real drift the agent never reached: decision 0017
says the publish job is skipped when the audit fails, and
`knowledge-audit.yml` now runs it unless the run was cancelled
(`jobs.publish.if` is `!cancelled()`).

Fixed on the way: `**/` in a glob now also matches no folder; a file step
sees markdown files (that one exists is not its content); an answer list
sent as JSON text is read; both check prompts now say to guard a function
against a missing key (`[?uses && starts_with(uses, ...)]`), which a test
in `tests/test_checks.py` backs. Still open: prompt files under
`.github/prompts/` and `action/prompts/` are markdown, so checks cannot read
them; only `.okf/` and `docs/` should be off limits. Jev answers at
`https://api.typesafe.ai/v1/systemone` (`scripts/probe/jev.py` asks it one
question).

## How far steps 4 to 7 get (2026-11-10)

`scripts/pilots/funnel.py` counts all 187 claims through the steps, from the
saved results (no calls): 8 settled free; 110 with lines shown, of which
Clef calls 72 "enough" and 38 "not enough"; 69 with no lines, of which Clef
calls 17 not about the code now and 52 left for the searching agent. On the
30 sampled claims the grouped one call made a check that holds for 11 of 17
"enough" (4 more unanswered: unreadable replies) and 4 of 11 "not enough".

## Decision-model questions before extraction and routing (2026-11-10)

`scripts/pilots/questions.py` asked Clef and Jev the questions from the list
and scored them against labels we already have: the 219 hand-labelled
sentences of `../audit-agent/gold.jsonl` (190 with a clear label, 135 of them
checkable) for the extraction questions, and for routing, the quantifiers
of the 77 claims that sit in labelled sentences plus the checks the one-call
pilots wrote (24) and whether they hold (28). AUC: the chance that a random
yes ranks above a random no, so 0.5 means no signal. Jev cost about $0.08
(812 calls); Clef is free.

| Before extraction | Clef | Jev |
|---|---|---|
| "When" = current predicts checkable | **AUC 0.97**; history: 4 of 34 checkable | 0.93; history: 2 of 31 |
| "Could the files confirm it?" | 0.93 | 0.79; above 0.5 for 189 of 190, so it never drops anything |
| Kind is point or structural | 0.92; matches the hand label 105 of 219 | 0.82; 96 of 219 |
| Audience "anyone" means not checkable | 0.84 (4 of 29 checkable) | 0.78; picks "anyone" for only 4 |
| Specificity (score) | 0.77 | 0.78 |
| Restates an earlier sentence | 0.49; never says yes | 0.62; yes for 3 |

Rules for dropping a sentence before the extractor sees it, Clef:

| Drop when | Sentences dropped | Checkable claims lost |
|---|---|---|
| "could confirm" below 0.2 | 18 of 190 (9%) | 0 of 135 |
| not current and "could confirm" below 0.5 | 43 of 190 (23%) | 4 of 135 (3%) |
| "when" is not current | 56 of 190 (29%) | 10 of 135 (7%) |

The same rules on Jev drop next to nothing or lose 20 checkable claims, so
the gate is Clef's.

Routing labels are thin, so these are signs, not results: 4 claims with a
"none" quantifier, 7 with "all", one check with a negative step, one with
`expect: every`.

- Scope: when Clef picks "every", the sentence is an "all" (2 of 2), but it
  calls 3 of the 7 "all" claims "one". Jev: 3 of its 13 "every" are.
- What the claim names: 15 (Clef) and 17 (Jev) of 24 checks use the step the
  named thing suggests (a file gets a file step, a config key a query).
  Jev's "names something" predicts a check that holds (AUC 0.81); Clef's
  does not (0.48).
- Depends on another claim: Clef says yes for 84 of 187, too often to sort
  on; a low answer goes with a check that holds (0.72 on 28).
- Stakes (score): 167 and 168 of 187 land on "misleading" for both models,
  so it sorts nothing.
- Negative: nothing to score it against yet.

## A code step: matching code by shape (2026-11-10)

`checks/steps.py` has a `code` step: an ast-grep pattern such as
`subprocess.run($$$A, timeout=120)` matched in Python, shell, JavaScript,
TypeScript, Go, Rust, Java or Ruby files. It ignores comments, strings and
line breaks. ast-grep alone does not let a trailing `, $$$B` match nothing,
so the step also tries the pattern without it; a pattern that parses in
none of the files' languages fails as "could not run", so a broken pattern
never passes as "absent". Tests in `tests/test_checks.py`.

Same 30 claims, grouped one call, before and after the step was in the
prompt (`oneshot.py grouped --sample lines --tag code`; counts of grep steps
from `scripts/pilots/grep_on_code.py`):

| | Without | With the code step |
|---|---|---|
| Hold / fail / reason / unanswered | 17 / 5 / 4 / 4 | 17 / 3 / 2 / 8 |
| Grep steps over source code | 38 of 44 | 16 of 24 |
| Code steps | none | 14, in 20 checks; 13 match real code lines |
| Tokens a claim | 2.5k | 2.9k (more output) |

The model takes the step at once and writes checks that match code rather
than a line's text: `p.add_argument("--min-severity", choices=SEVERITIES,
default="high", $$$A)` instead of a regex. Fewer checks fail. The eight
unanswered are one group of eight claims that came back with empty answers;
the run before answered that group, so a retry of an empty group is the fix,
not the step. Failing grep checks mostly guessed code they were never shown
(`stale_after = stale_after_time(`); a code step guesses the same way.

A review found that "code matches nothing" passed for broken or misread
patterns (`timeout=120` is an assignment in Python; a Python typo over a glob
with shell files), so the step tests presence only; absence is grep's job.
Go is out: its call patterns parse but match nothing. In shell and Ruby,
`$NAME` is that variable and must capture exactly itself. Known limits: in
shell a command with more arguments after the pattern still matches, and
lowercase Ruby globals never match.

Tree-sitter stays in `settle_claims.py`: it finds definitions in every
language with one walk, where ast-grep would need a pattern per language.

## Shrinking what the agent gets (2026-11-10)

52 claims (`scripts/pilots/no_lines.py`) reach the searching agent: the
settle step showed no lines and Clef calls them about the code now. They
name no file or symbol ("the CI audit's checkout keeps no credentials").
The agent costs about 23k tokens a claim, 95% of it input: its history is
sent again every turn (460k in, 23k out over the three batches measured).

`scripts/pilots/dossier.py` finds lines for them with no model: the files
the claim's concept is about (its `sources` front matter, the files its text
names, the files its other claims located), the code files that register a
command it names, then BM25 over 40-line windows of those files with the
claim's words. All 52 get lines (44 from the concept's files, 8 from a
command's file).

Grouped one call with those lines (`oneshot.py grouped --sample agent`):

| | First run | With one retry of unanswered claims |
|---|---|---|
| Hold / fail / reason / unanswered | 7 / 10 / 14 / 21 | 23 / 8 / 14 / 7 |
| Tokens a claim | 3.3k | 5.4k (134k of the 281k is output) |

Graded by hand, the 23 that hold: 15 good, 4 fair (the names exist, the
behaviour is not tested), 4 weak (a comment's words, a word's absence, a
file's existence). None of the 8 failures is drift: wrong scope (a token
grep over all of `action.yml`), code the model guessed and was not shown,
a file step on `.okf/`, a query over a claim about another repository. So
the one call settles about 19 of the 52 at 5.4k a claim, and the agent's
share drops to about 33.

The unanswered answers came back flat: DeepSeek put `steps`, `strength`
and `why` beside `claim` instead of under `check`, in groups of seven or
more. `oneshot.py`'s `Answer` now reads that shape too (not yet rerun).
Output, mostly reasoning at low effort, is now half the one call's tokens.

## The agent's own spend: lines up front, history not rewritten (2026-11-10)

`scripts/pilots/agent_spend.py` runs the agent on a fixed 8 (seed 7) of the
15 claims the grouped one call with dossier lines failed or left unanswered.
"after" puts each claim's dossier lines in the first message and turns
trimming off (`Budget(trim=False)`), so each call's input starts with the
last call's and the prompt cache can serve it; "before" is the agent as it
was. The writer now counts cached input tokens (`BatchResult.tokens_cached`).

"after" passed the cap after two batches (7 claims) and saved nothing; every
call was traced, so `scripts/pilots/from_traces.py` and
`scripts/pilots/agent_spend_traced.py` rebuilt it from LangSmith. The cap
then left room for "before" on the first batch only, at an 80k budget.

| First batch (4 claims) | Before | After |
|---|---|---|
| Calls | 8 | 9 |
| Input / cached / output | 78k / 41k (52%) / 3k | 129k / 97k (75%) / 6k |
| Not cached, a claim | 10.1k | 9.4k |
| Finished | **0 of 4** | **4 of 4** |

Over both "after" batches: 7 of 7 finished, all checks hold; graded by hand
5 good, 2 fair (a generic `return None` grep; a tool list as proxy for "no
commit"). 37k tokens a claim in all, 9.1k not cached: the dossier rides in
every call, mostly from cache. Of 34 tool calls, 23 were TryCheck: with the
lines up front the agent checks rather than searches.

"before" ran out of tokens and stopped with no Submit, so all four came back
unfinished: the last submit-only call fired only on turns, never on tokens.
It now also fires once the next call, guessed as the last call plus its
growth, would pass the token budget; a batch can still pass the budget by up
to one normal call plus the last call (tests in `tests/test_check_writer.py`;
reviewed).

So in tokens counted the "after" agent costs more (37k against the old
pilot's 23k a claim), and in tokens not served from cache a little less
(9.1k against 10.1k), while finishing every claim. What it costs depends on
what a cached token costs: DeepSeek's own price for one is about a tenth.

## Code tools for the agent, a last-call fix, and a two-call writer (2026-11-10)

The agent got two tools that read code structure, both on ast-grep:
CodeSearch (an ast-grep pattern in, matching lines out) and Outline (a
file's functions and classes, or a YAML file's keys, with their lines), and
optional prompt hints for the syntax it kept failing on (an `elif` or
`except` clause is no pattern alone; flatten `jobs.*.steps[]` before
filtering; `paths` is one string). `scripts/pilots/agent_spend.py --all`
runs each variant on all 15 left-over claims, five batches of up to four.

Round one (`agent-spend-*-all.json`) was spoilt by the last call: in 7 of
20 batches DeepSeek called TryCheck inside the submit-only call, or sent its
checks as JSON text, so the whole batch came back unfinished. `_final` now
reads a Submit among other tool calls, `Submit` reads a list sent as JSON
text, and an unreadable last call, or one naming none of the open claims, is
made once more.

Round two (`agent-spend-*-all-r2.json`, `scripts/pilots/run_round2.sh`):

| Variant | Hold / fail / reason / unfinished | Tokens a claim | Not cached |
|---|---|---|---|
| before: no lines, trimmed | 6 / 1 / 1 / 7 | 41.8k | 16.8k |
| after: lines, not trimmed | **13 / 2 / 0 / 0** | 38.0k | **6.9k** |
| hints: after, code tools, hints | 11 / 1 / 2 / 1 | 31.9k | 7.7k |
| bare-tools: code tools and hints, no lines | 11 / 3 / 0 / 1 | 36.9k | 11.8k |

The agent hardly touches the new tools: one Outline call in 35 turns with
lines up front, one CodeSearch and one Outline in 48 turns without. With
lines it checks rather than searches; without, it still greps and reads.
So the tools change nothing measurable here. The "before" agent still lost
two batches at the last call (one Submit naming none of the open claims,
which now retries; one whose JSON text did not parse).

The two-call writer (`oneshot.py grouped --sample agent --fix`): one call per
group with dossier lines, the checks run, then one call per group with only
the failing checks, what each step saw, and the lines. On all 52 claims the
agent would get: 36 hold, 2 fail, 14 reasons, 5.2k tokens a claim (the fix
calls 85k of the 268k). The fix call turned 10 of 12 failing checks into
ones that hold. Graded by hand: 4 good, 4 fair, 1 weak, and 1 that bent the
known drift into a pass: "when the audit job fails, the open issue stays as
it was" first failed on `jobs.publish.if` being `!cancelled()`, and the fix
asserted `!cancelled()`. The fix prompt now says never to change what a
check expects to what the repository has.

Rerun with that rule (`--tag nobend`): 35 hold, 1 fails, 16 reasons, 5.5k
tokens a claim; the fix call again turned 10 of 11 failures into passes. On
the drift claim it now argues instead of bending: its check pins
`if: ${{ !cancelled() }}` but adds that the issue-posting step needs the
failed audit's report, marks it a proxy and says why ("they do not prove the
agent never leaves a report behind on failure"). The claim is arguable
rather than plainly false, so a person should read it; a check that changed
what it expects after its first run is worth flagging for that.

So for the claims that name nothing, the two-call writer does what the
agent does at about a seventh of the tokens (5.2k against 38k a claim) and
with no turns; the agent stays for what both leave failing.

## Decision models after the check: sorting failures, judging claims (2026-11-10)

**Sorting failures** (`scripts/pilots/failures.py`, `failure_judge.py`). All
72 failing checks the pilots wrote, labelled by hand against the repository
(`failure_labels.json`): 3 drift (all one claim: the publish job is not
skipped when the audit fails), 3 arguable (left out), 66 wrong checks. Asked
"does what the steps saw show the claim is false, rather than the check
being wrong?":

| | AUC | Drift checks ranked (of 69) | Above 0.5 |
|---|---|---|---|
| Clef | 0.86 | 1, 2, 30 | 2 of 3 drift, 2 wrong checks |
| Jev | **0.98** | **1, 2, 8** | 2 of 3 drift, 4 wrong checks |

Reading Jev's top 8 would have caught every drift check here; but the three
are one drift, so this is one case seen three times.

**Judging a claim from its lines** (`claim_judge.py`). 29 true claims (exact
checks that hold, and four prompt and skill claims read by hand), 28 false
twins DeepSeek wrote (one detail changed, read by hand; one muddy twin left
out) and one claim false in fact: the okf-bundle rule never mentions
`kmctl verify`. Each shown with the same lines (the settle step's or the
dossier's; for prose, the prompt or skill file, which checks cannot read).

| Group | Items | Clef AUC / right | Jev AUC / right |
|---|---|---|---|
| Prose | 9 | 1.00 / 7 | **1.00 / 8** |
| Point | 30 | 0.93 / 23 | **0.95 / 26** |
| Structural | 15 | 0.84 / 8 | **0.90 / 12** |
| All | 58 | 0.93 / 40 | **0.93 / 50** |

"Right" counts the most likely verdict of true, false or not shown. Both miss
the same kind: absence and "only" over files the lines do not show ("no
longer exists", "the only step given the token"), which a decision model
cannot see and a check can. On the real false prose claim both say not
shown rather than true. The twins change one detail of a claim whose lines
were picked for it, so they are easier than drift found in the wild.

## `audit checks`: the pipeline in the CLI (2026-11-10)

`audit checks diff | write | run | triage` (`src/audit_cli/checks_cli.py`,
`src/audit_cli/checks/`): settle free (`anchors.py`), find lines
(`lines.py`), the two-call writer (`twocall.py`), the agent behind
`checks.agent`, runs with no model (`steps.py`), and a decision model over a
generic `[decisions]` endpoint (`decide.py`) that ranks failures and judges
reason-only claims. Migration 0004 stores each claim's check, the files it
read with content hashes, its last result, triage answers, a cache (the CLI
`--help` walk) and every pass with its tokens per stage.

Nothing is redone for nothing: a claim's id follows its text; a check runs
again only when a file it reads changes (a glob is matched again each run);
a check is written again only when new, when triage called it wrong, or for
a reason whose files changed; settled claims are settled again by every
run, free. A reason never replaces a failing check (fix call, agent or
`--rewrite-failing`), and a fix that changes what a failed step expects is
flagged. Help steps run only pyproject scripts and argparse scripts. A
reason whose lines came from no file is never decided again until its claim
changes.

On kmctl's 183 claims (`scripts/run_checks.sh`, DeepSeek at low effort, Jev):

| Pass | What happened | Model | Seconds |
|---|---|---|---|
| write | 8 settled, 175 written: 42 calls, then 16 fix calls on 30 failing (13 then held, 1 flagged); 8 unanswered | 868k tokens (336k + 91k in, of which 176k cached; 442k out): 5.0k a claim | 896 |
| write again | only the 8 unanswered: 4 hold, 1 fails, 3 reasons | 13 calls | 69 |
| run | 136 checks reused, 8 settled again: 127 hold, 17 fail, 39 reasons | none | 0.6 |
| triage | 17 failures ranked, 39 reasons judged | 56 Jev calls | 4.4 |

Jev's top four failures: the known drift twice (decision 0017: the publish
job runs unless the run was cancelled), a claim that states a risk the
code has since closed (a poisoned uv cache; rationale extracted as a
current fact), and a wrong check (it grepped `*.yml` for Hermes, whose
workflows are `.yaml`; the writer had called it drift too). Judging
reason-only claims called the okf-bundle rule claim true at 0.95, which is
false: `.claude/` is left out by `[files]`, so the rule itself was never
shown. Every model and decision call sat inside the CLI's spans in LangSmith
(`scripts/pilots/from_traces.py --run-type chain`).

## Strategies from *AI Agents: The Definitive Guide* (2026-11-10)

Read from the book's OKF bundle (`~/Documents/ai-agents-koenigstein/.okf`,
Nicole Koenigstein, O'Reilly 2026): its summary, the strategy catalog, and the
full When / How / Why entries of the 26 strategies that fit this audit. Each
row names the chapter file in `~/Documents/ai-agents-koenigstein/.okf/chapters/`.

**What `audit checks` already does**

| Strategy | Chapter | Where it is here |
|---|---|---|
| Let hard checks do most of the work; keep LLM judges for open-ended output | `09-customized-and-advanced-evaluation.md` | Checks run with no model; the decision model only ranks failures and judges reason-only claims |
| Add validation gates after each generating step | `05-production-contracts-and-mcp.md` | Every written check runs at once; only failures go to the fix call |
| Separate discovery from execution across runs | `06-secure-execution-and-tool-governance.md` | Write once with a model, run many times with none |
| Memoize decisions over fully conditioned state | `11-compute-and-cost.md` | A check is keyed by its claim text and the content hashes of the files it reads |
| Normalize labels inside Pydantic validators | `07-deploying-agents-in-products.md` | `twocall.Answer` reads flat answers; `Answers` and `Submit` read lists sent as JSON text |
| Retry only on 5xx (and 429) with jittered backoff | `07-deploying-agents-in-products.md` | `decide.Decider` (tenacity) |
| Circuit breaker with turn and budget fuses; a context janitor | `07-deploying-agents-in-products.md` | The agent's `Budget` (turns, tokens, a last submit-only call); `Budget.trim` |
| Bound the tool loop and force a final answer | `01-from-llms-to-agents.md` | `writer._final`, tried twice, reading a Submit beside other tool calls |
| Feed failures back to the model | `05-production-contracts-and-mcp.md` | The fix call sees each failed step and what it saw (raw, see below) |
| Pin the prompt and keep an audit trail | `05-production-contracts-and-mcp.md` | Each check stores its writer, prompt hash and commit; each pass is recorded with its spend |
| Keep judge answers as an audit trail | `09-customized-and-advanced-evaluation.md` | `check_triage` stores every answer with what was asked (`asked_key`) |
| Make execution observable | `01-from-llms-to-agents.md` | LangSmith spans per command, with every model and decision call inside them |
| Cap reasoning | `04-models-behind-the-agents.md` | `reasoning_effort = "low"` (default thinking cost 4x the tokens) |
| Default-deny the tool surface | `06-secure-execution-and-tool-governance.md` | Help steps run only pyproject scripts and argparse scripts; checks read only `[files]`-allowed files |

**What it could do next, in the order of what it would buy**

1. **Mutation-test every check** (`09-customized-and-advanced-evaluation.md`:
   SWE-smith, combining bug-generation methods). Change the code a check
   reads in scripted ways (flip a matched value, rename a matched function,
   delete a matched line, change a YAML value) and see whether the check
   notices. A check that survives every change is hollow. No model; it gives
   every check a quality score in place of hand grading, and catches a fix
   that bent a check, since a bent check does not notice changes to the line
   it was meant to test.
2. **Gate the score behind the hard check** (`03-advanced-planning-and-reasoning.md`:
   hybrid reward). Trust "holds" fully only when the check also catches
   mutations; rank triage by the run result together with the decision
   model's score.
3. **Feed back meaning, not raw errors** (`05-production-contracts-and-mcp.md`).
   The fix call now gets "could not run: ValueError: the pattern does not
   parse as python"; one sentence the model can act on ("an except clause
   cannot stand alone: match the whole try") aims at the syntax traps behind
   most failed fixes.
4. **A normalized, then semantic, cache for claims** (`11-compute-and-cost.md`:
   tiered cache; never cache failed outputs). A reworded claim gets a new id
   and is written from scratch. First look for an old claim of the same
   document with the same normalized text, or about 0.9 similar; run its
   check and keep it if it holds. Never reuse a failing one.
5. **Thinking per step** (`04-models-behind-the-agents.md`: toggle thinking).
   Output is half the writer's tokens: thinking off for the write call (the
   lines are given), on for the fix call (it must diagnose). A config split,
   to measure.
6. **A regression bench from the labels** (`08-foundational-evaluation-and-observation.md`,
   `09-customized-and-advanced-evaluation.md`: promote failures to a
   versioned suite). Freeze the hand-labelled failures, the false twins and
   the graded checks as a versioned file, and rerun them at temperature 0
   before changing the prompt, model or group size: a release gate.
7. **Estimate cost from expected calls** (`11-compute-and-cost.md`). Have
   `checks diff` print expected tokens from the measured rates (groups, fix
   rate, agent rate), which fits agreeing a budget before a long run.
8. **Hash the settings, not only the prompt** (`05-production-contracts-and-mcp.md`:
   pin and hash the policy at start). Store a hash of model, effort and group
   size with each check and pass.
9. **Threats with no attacker, and trust-aware input** (`12-threat-modeling.md`).
   In the GitHub Action, claim text can come from a pull request and goes into
   the prompts; a planted claim can at worst steer the writer to a hollow
   check, which mutation testing (1) catches. Tracing sends repository code to
   LangSmith: for a private repository, redact, or sample all errors and 10 to
   25% of successes (`07-deploying-agents-in-products.md`).
10. **Make judges fail soft** (`03-advanced-planning-and-reasoning.md`). A
    triage question that errors is left out of the ranking today; a neutral
    0.5 would keep it visible.

## Tracing setup

LangSmith reads its own variables. The key is in the shell (`~/.zshrc`); the
endpoint (LangSmith EU), agent id and environment are in this folder's
`.env`, git-ignored, which the CLI loads from the working folder. Without the
endpoint the SDK sends to the US endpoint, which refuses an EU key with 403.

## One command, trust scores, per-question decisions, background runs (2026-11-10)

- **Any folder.** Commands on stored claims (`claims list`, every `checks`
  verb) take any folder of the repository; a bundle, a concept file or a
  folder inside the bundle that holds claims narrows them. The bundle is
  found by its `index.md` with `okf_version` (`processing/target.py`
  `resolve_project`).
- **`audit checks run`** takes every claim to a verdict: writes what needs a
  check (new, or judged wrong), runs everything, and asks the decision
  questions switched on. `--no-write` runs stored checks only. `list` shows
  each claim's status and trust; `--status weak --details` the holding checks
  that only look good.
- **Trust scores.** Mutation testing (`checks/mutate.py`, no model): each
  holding check runs on small in-memory changes to the code lines it matched
  (a flipped boolean, a renamed definition, a replaced value, a deleted
  statement); comments and docstrings are never changed, and a check that
  matched only text is weak. On kmctl, 25 of 161 measurable holding checks
  noticed no change, 21 of them proxy greps for a name or word
  (`scripts/pilots/mutation.py`). The link score asks the decision model
  whether a check tests the claim, a nearby fact, a keyword or nothing.
- **Decisions per question.** `[decisions.providers.NAME]` holds endpoints;
  `[decisions.failure]`, `[decisions.judge]` and `[decisions.link]` are each
  switched on with their own provider and model, all off by default. An
  answer's key includes its model, so a new model asks again.
- **Background runs.** `run --background` starts a detached run; `status`
  shows its stage, claims done, tokens and errors; `stop` ends it. One run or
  write per project at a time: the slot is taken in one SQLite transaction,
  and a job's process is known by its id and start time, so a reused id does
  not hold it. A model call that fails (a 504, a timeout) loses its group
  only; those claims are retried next run.

The full run on kmctl's 255 claims: 81 written in 9 minutes for 525k tokens
(6.5k a claim, every claim answered); then 181 hold, 22 fail, 52 reasons.
Triage's top five are the known drift twice, a rationale claim, a wrong check
and a claim about `docs/`, which checks never read.

## Resolving weak checks (2026-11-10)

- **Weak, unsure, accepted.** A holding check is weak when it is hollow (it
  noticed none of its mutants, or matched only text) or off the claim (link
  under 0.5). It is unsure when the two scores disagree: hollow but scored
  0.75 or more on link, or off the claim but it noticed a change.
- **Strengthen.** `checks run` ends by rewriting each weak check once, with
  what the mutants showed it missed. A rewrite is kept only if it holds,
  notices more changes to a value or condition than the old check (a deleted
  line or file breaks any check that reads it, so those do not count), is not
  only file steps where the old one was not, and, with link on, scores 0.5 or
  more and no lower than the old check.
- **Automatic acceptance.** A rewrite that is no better leaves the old check,
  accepted by `auto` with the reason, until its code changes (mutation scores
  are keyed on the code they read). A claim the model left unanswered, or a
  rewrite the decision model failed to score, is tried again next run, not
  accepted.
- **By hand.** `audit checks accept CLAIM_ID --note WHY` accepts a check that
  cannot be done better; `--undo` lets it be tried again. `audit checks write
  --claim CLAIM_ID` writes one claim's check afresh, and never swaps a failing
  check for a reason.
- **Mutation version 3.** Backtick JSON literals in a yes/no query are read,
  so the lines holding the values it compares are changed; `true`, `false`,
  `null` and numbers are dropped. The version is part of the score key, so
  every check is scored again on the next run, with no model calls.

Not closed: with link off, a rewrite that tests an unrelated line holding a
value can still count as better. Keep link on while strengthening.

## Claude as the checker, on 60 claims (2026-11-10)

`scripts/pilots/claude_review.py` drew 60 stored claims: the 28 with a pipeline
verdict and 32 unchecked point or structural claims (seed 7). Four Claude Opus
reviewers, blind to the pipeline's answers, judged each claim worth checking or
not, then checked it by reading the repository, with file:line evidence
(`results/pilots/claude-review/`).

- **Cost:** 308k tokens for 60 claims (5.1k a claim, about what DeepSeek
  spends writing a check), 2.5 minutes with four in parallel.
- **Worth checking:** 53 of 60; 5 about outside tools (APM, GitHub), 1
  history, 1 vague.
- **Against the pipeline's 28:** 19 agree. Of the 9 that differ, the reviewer
  was right on each one looked at:
  - 2 false failures. A grep over `*.yml` missed `hermes-*.yaml`, and a query
    guessed the key `OLLAMA_API_KEY` where the workflow sets `AUDIT_API_KEY`;
    triage ranked the first as drift.
  - 2 missed drifts. The claim names two test files and only one asserts it;
    the check looked in that one only.
  - 4 reasons where the answer was in the code (`verify.py:163` for `at`).
  - 1 holding check on GitHub's behaviour, not the repository's.
- **Unchecked 32:** 3 false (a `Finding` has no `evidence` field; not every
  verb calls one module; `kmctl mv` does update `checked.against`).

Not checked by a person. A verdict is a judgment made once; a check is rerun
free on every commit, so the reviewer's answers do not replace checks.

**Haiku on the same 60** (`compare --model haiku`): 326k tokens (5.4k a
claim), 2 to 2.8 minutes. It agrees with Opus on 46 of 60 and catches both
false failures. Of the 14 differences:

- Haiku is stricter and more consistent where it is right: it calls all four
  "two test files" claims false (Opus called two of the four true), and leaves
  `OLLAMA_API_KEY` "in the environment" unsettled where the key goes in as an
  action input (Opus said true while its own evidence said it cannot be seen).
- Opus reads deeper: Haiku leaves 3 claims unsettled that Opus settles, calls
  `at` "used to decide what changed" where it only finds the entry (wrong),
  and reads the installed `.claude/rules` copy instead of the shipped rule.
- Five calls on outside tools (APM, GitHub, copier): Haiku marks them true
  from docs and tests that restate them; Opus skips them as not this
  repository's to show. Opus's call is the stricter one.

## Open

- The project's `.venv` sits inside `.okf/`, and the strict OKF validator
  reads the markdown files of installed packages as concepts, so the
  `okf-validate` hook fails while it exists. A clean checkout passes.

## Tests

`uv run pytest` (99 tests, real git repositories and SQLite files in
temporary folders; a stand-in replaces the paid model). `uv run ruff check`
and `uv run mypy src tests` (strict) pass.
