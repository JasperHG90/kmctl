# decision-gaps: skill-creator results

Made with the skill-creator skill (ADR 0007), 2026-11-16. Each run worked in
its own throwaway clone of kmctl's repository at `dd1158d3`, by a Claude
Opus 5.5 subagent, with and without the skill; `kmctl` meant `uv run kmctl`
in the clone. Grades are against each case's `graders/`. The known-answer
counts use the labels in `.okf/prototypes/decision-gaps/results/labels.json`:
of the 59 changes since `2cf55821c`, four labelled gaps (`ce8b712c` and
`da6a34c5`, the MIT licence; `09af291c`, actions pinned to SHAs; `c92c6e0d`,
CI's collecting `tests` job) and one labelled false alarm (`642d7236`,
`kmctl doctor`'s warn outcome). Claims on changes the labels do not cover
are listed, not scored.

## known-range-finds-labelled-gaps

| Round | Skill | Assertions | Labelled gaps found | Labelled false alarms raised | .okf/ |
|---|---|---|---|---|---|
| 1 | without | 5 of 7 | labelled gaps found: 4 of 4 | labelled false alarms raised: 1 of 1 | .okf/ unchanged |
| 1 | with | 6 of 7 | labelled gaps found: 3 of 4 | labelled false alarms raised: 0 of 1 | .okf/ unchanged |
| 2 | with | 5 of 7 | labelled gaps found: 3 of 4 | labelled false alarms raised: 0 of 1 | .okf/ unchanged |
| 3, run 1 | with | 7 of 7 | labelled gaps found: 4 of 4 | labelled false alarms raised: 0 of 1 | .okf/ unchanged |
| 3, run 2 | with | 7 of 7 | labelled gaps found: 4 of 4 | labelled false alarms raised: 0 of 1 | .okf/ unchanged |

- Round 1, with the skill, called SHA pinning the extension of an earlier
  practice and left it out. Round 2 added that an unrecorded practice's
  change still counts, and that stability promises count; it found SHA
  pinning and kmaudit's beta marking but dropped the CI collecting job as
  "tooling layout" and listed `a4c175d9`, which amends ADR 0012, as missing.
- Both rounds had the orchestrating agent write its own instructions for
  each batch judge, which drifted. Round 3 moved the judging into
  `references/judging.md`, handed to every batch judge as is, and said that
  a change with a non-empty `recorded` is covered and that CI and required
  checks count. Both round-3 runs found all four labelled gaps and raised
  no labelled false alarm.
- Unlabelled claims in round 3, for the user to judge: kmaudit marked beta
  (`2063727d`, both runs), and the release rule's `--admin` ban and
  notes-fixing method (`64137973`, `a6e2df02`, run 1). The baseline raised
  the beta marking, feedback ownership on the audit page and kmaudit's
  install hints.
- Without the skill, the agent found `kmctl decision candidates` through
  `kmctl decision --help` and used it, so the baseline is stronger than a
  bare model. It raised `kmctl doctor`'s warn outcome and did not say the
  user decides what to record.
- One round-3 run had the harness refuse its Write tool for `report.md` in
  the scratch folder and wrote it with a shell heredoc instead; its clone
  stayed clean.
- Time and tokens, round 3 with the skill against the round-1 baseline:
  152 s and 77k tokens a run against 222 s and 94k.

## default-range-recent

| Round | Skill | Assertions | .okf/ |
|---|---|---|---|
| 1 | without | 4 of 4 | .okf/ unchanged |
| 1 | with | 4 of 4 | .okf/ unchanged |
| 2 | with | 4 of 4 | .okf/ unchanged |

The default range held one change, `dd1158d3`, covered by the ADR 0047 it
adds. Without the skill the agent widened the range to a week on its own
and reported two gaps; with it, round 2 said the range was short and
offered the nine changes since `v0.13.0`. The case does not tell the two
apart. It was not rerun on round 3's skill.

## write-named-record-no-scan

| Round | Skill | Assertions | .okf/ |
|---|---|---|---|
| 1 | without | 2 of 2 | a new ADR 0048, as asked |
| 1 | with | 2 of 2 | a new ADR 0048, as asked |

Both wrote the MIT record with `kmctl new decision` and neither ran
`kmctl decision candidates`. The case does not tell the two apart either;
it shows the skill stays out of the way when the user names the decision.
It was not rerun on round 3's skill.

## Triggering

`trigger-queries.json` holds 16 queries, 8 that should use the skill and 8
near misses. `run_eval` (3 runs a query) from an empty folder: every near
miss stayed silent, and 2 of the 8 should-trigger queries triggered at all,
each in 1 of 3 runs. `run_loop` (5 rounds, 10 training and 6 held-out
queries) from a clone of the repository kept precision at 100% and moved
held-out recall between 11% and 22%; it chose the original description as
best. The shipped description keeps that text after a new first sentence,
which the briefing shows, and a shorter second one; the loop was not
rerun on it. The skill rarely triggers on its description alone in
`claude -p`. In a kmctl repository the session briefing names each skill with
the first sentence of its description ("Report the changes in git history
that made an unrecorded decision."), which these runs do not load; a user
can also name it (`/decision-gaps`). The plan's test that the description
triggers on asks to find unrecorded decisions is not met by the description
alone.
