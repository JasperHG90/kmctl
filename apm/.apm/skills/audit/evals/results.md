# audit: skill-creator results

Made with the skill-creator skill (ADR 0007), together with the
`kmctl-auditor` agent and the three review skills it follows. The two prompts
in `evals.json` ran on two real bundles:

- `/audit the decision log` on a copy of this repository (9 records), with the
  skill and without it.
- `/audit the architecture docs` on loop-harness at `/home/vscode/workspace`
  (10 pages), read only, with the skill and without it.
- `/audit the practices` on loop-harness (8 pages), with the skill only, in
  iteration 2.

In the runs with the skill the agent was not installed, so the run did the
agent's job itself from `plugin/agents/kmctl-auditor.md`, reading only.
`sample-findings.json` is the findings block from the iteration-1
loop-harness run.

## Iteration 1

kmctl decisions: 8 holds, 1 unsure. The baseline found what the skill
missed: every record carries `decision_status` and `decided_on`, which no ADR
allows (I4, ADR 0009); seven records have no Consequences section; and ADR
0002 says the briefing names skills, which it does not.

loop-harness architecture: 6 of 10 drifted. An independent check of each
drifted claim against the code found all 6 pages really drifted (12 claims
real, 0 false). That check found nothing more on the two holds pages it
re-checked (lifecycle and release), but iteration 2 found real drift on both,
so the holds verdicts were wrong. The baseline (128k tokens, 498 s, no
findings block) called 8 of the 10 pages drifted, plus `index.md`, which is not
a concept. What
it caught that the skill did not was mostly lists the page presents as
complete that miss items.

Changes: the decision review checks every claim in a record, its required
sections and any field no ADR allows, and links both ways; the architecture
review checks that a list presented as complete is complete; the agent may not
call a page holds when it checked only part of it.

## Iteration 2

kmctl decisions: 9 drifted, 0 holds. It found all three things the baseline
found, with a substantive drift in ADR 0002 and missing sections or unapproved
fields in the rest. The ticket `adr-audit-fixes` fixes them.

loop-harness architecture: 10 of 10 drifted, four of them by one small item.
An independent check (`verification.md` in the run's folder) split the
findings into 34 claims: **31 real, 0 false, 3 weak** (true but trivial, or a
list the page does not present as complete). All 10 pages have at least one
real claim. It now catches the incomplete lists the baseline found, and the
findings block parses in the shape `sample-findings.json` shows.

loop-harness practices: 1 drifted, 6 unsure, 1 holds. The drifted page
states a lesson with no exceptions, and a later ADR (0035) made one; the page
does not mention it. The six unsure pages rest on counts from v1 files that
are not in the checkout, so the agent said what it would need instead of
guessing, which is what the practices review asks. The holds page's figures
all match a prototype that can rerun them.

## Limits

- Both bundles are small (9 records, 10 pages): one batch each, so batching
  across several agents was not exercised.
- One run per configuration, so no variance figures.
