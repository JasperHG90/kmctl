---
type: prototype
title: "Decision gaps"
description: "Whether a no-model filter plus an agent judge finds merges that made a decision nobody recorded, measured on this repository's history: the judge found 25 of 30 hidden decisions (83%); of its 32 claims on other changes, 15 were choices the change recorded as an amendment and 10 of the other 17 were real gaps (59%), for $3.19 over 161 units, so kmctl decision gaps and its skill are worth building."
tags: [prototype, decisions, history]
generated:
  by: process:kmctl/0.13.0
  at: 2026-11-16T13:47:54Z
verified:
  - by: human:jasper
    at: 2026-11-27T20:41:27Z
---

# Decision gaps

## Question

Can kmctl find, in a repository's git history, the changes that made a
decision nobody recorded? The approach under test: a command with no model
splits history into units and ranks them by decision-shaped signals, and an
agent judges each unit. Built in kmctl, as
[ADR 0046](../../decisions/0046-kmctl-works-from-code-toward-knowledge-and-kmaudit-from-knowledge-toward-code.md)
places it, if the numbers clear the bars set before the judge ran: recall
of at least 70% with the 95% interval's lower end at least 50%, precision of
at least 50%, and at most $10 to judge the whole range.

## Method

This repository is its own ground truth, over `14799749..ee87e883` (after
ADRs 0007 to 0009, up to the badges merge).

1. `scripts/units.py` walks `main`'s first-parent line as
   `scripts/release_notes.py` does, syncs and ticket-carrying pull requests
   expanded, and keeps one unit per ticket merge, pull request or plain
   commit: 161 units. A unit is positive when it adds a decision record
   whose number its first parent lacks: 31 units, ADRs 0010 to 0045.
2. `scripts/hide.py` hides the answer the same way for every unit: no path
   under `.okf/` or `.loop/`, and no sentence of the subject, message or
   plan intent that names an ADR, a decision, a record, `.okf/`,
   `summary.md`, `log.md`, "next free" or "the number". ADR 0030's unit
   changes nothing else, so it only records a choice made elsewhere and is
   reported apart, out of the recall count: 30 positives count.
3. `scripts/leak_check.py` tests the hiding with detectors that share
   nothing with it: visible bookkeeping paths separate positives from
   negatives at AUC 0.50 (chance), and a separate list of record-keeping
   words at AUC 0.64; it prints the words that differ most, led by "entry", "bundle" and "summary". Decision-making tickets
   here often change the knowledge system itself; that residue may lift
   recall a little.
4. `scripts/signals.py` scores each unit on eight signals: a dependency
   line changed, a new source module, files deleted, a workflow, a config
   or schema file, a harness surface (skills, agents, hooks, rules), words
   such as "instead of", "replace", "drop", "no longer", and changes across
   four or more top-level folders.
5. `scripts/judge.py` runs `claude -p` (Sonnet) from an empty folder with no
   tools, MCP servers or settings, on every unit. It sees the stripped
   text, the plan's intent when the ticket has one, the visible files and
   the decision index as it stood in the unit's first parent, and answers
   `missing`, `covered` or `none` with the choice and the rejected option.
6. `results/labels.json` holds the labels, written by Claude (Opus 5.5),
   not the operator. Each `missing` on a positive was checked against the
   hidden ADR: all matched. Each `missing` on a negative is a gap (a choice
   with a rejected option no record covers), a false alarm, or recorded in
   the unit (the unit amends an existing ADR with the choice, which the
   judge could not see because `.okf/` was hidden; a real run sees it).
7. `scripts/score.py` prints every number below from `results/`.

```
python3 .okf/prototypes/decision-gaps/scripts/units.py . > .okf/prototypes/decision-gaps/results/units.jsonl
python3 .okf/prototypes/decision-gaps/scripts/signals.py . .okf/prototypes/decision-gaps/results/units.jsonl > .okf/prototypes/decision-gaps/results/signals.jsonl
python3 .okf/prototypes/decision-gaps/scripts/judge.py . .okf/prototypes/decision-gaps/results/units.jsonl .okf/prototypes/decision-gaps/results/judge.jsonl
python3 .okf/prototypes/decision-gaps/scripts/leak_check.py . .okf/prototypes/decision-gaps/results/units.jsonl
python3 .okf/prototypes/decision-gaps/scripts/score.py .okf/prototypes/decision-gaps/results
```

`units.py` imports today's `scripts/release_notes.py`, so a change to how
that script walks merges can change the units; `tests/test_decision_gaps_prototype.py`
fails when it does.

## Results

The filter alone, by score threshold:

| Score at least | Units kept | Hidden decisions caught |
|---|---|---|
| 1 | 128/161 (80%) | 29/30 (97%) |
| 2 | 83/161 (52%) | 25/30 (83%) |
| 3 | 54/161 (34%) | 23/30 (77%) |
| 4 | 29/161 (18%) | 17/30 (57%) |
| 5 | 13/161 (8%) | 12/30 (40%) |

The judge, on every unit:

| Measure | Value |
|---|---|
| Recall on hidden decisions | 25/30 (83%), 95% Wilson 66% to 93% |
| Missed | ADR 0019, 0031, 0033, 0034, 0042 |
| `missing` claims on the 130 other units | 32 (25%): 10 gap, 7 false alarm, 15 recorded in the unit |
| Precision (gaps among gap and false alarm) | 10/17 (59%), 95% Wilson 36% to 78% |
| Cost and time | $3.19 for the range, $0.020 per unit; 16 minutes, 6.1 s per unit |

The ten gaps it found are choices this repository never recorded: vendoring
a pinned okf validator for tests instead of depending on okf-skills, the one
index format `kmctl check` enforces, keeping the GitHub token out of the
model's CI step, the one kinds table behind `kmctl schema`, moving the
repository's own rules from aim to APM, running CI through the toiminnot
actions, the MIT licence (two units), pinning every action to a commit SHA
(recorded months later in ADR 0012's correction), and keeping `main`'s
required check through a collector job. The seven false alarms are
features or interface details (`kmctl doctor`, its warn outcome, a terminal
prompt, a starter question, a test tier, a pre-commit hook) and one choice
ADR 0001 already covered. The validator was first labelled a false alarm
and relabelled a gap after review.

Precision rests on labels, and its margin is thin. The plan defined a hit
as a correct claim; "recorded in the unit" is a category added after the
run, for claims the judge could not have seen the record of, and it is left
out of precision. Other readings, all printed by `score.py`:

| Reading | Precision |
|---|---|
| As labelled | 10/17 (59%) |
| The MIT licence, claimed twice, counted once | 9/16 (56%) |
| Recorded in the unit counted as correct, as the plan's rule reads | 25/32 (78%) |
| Recorded in the unit counted as false alarms | 10/32 (31%) |
| One gap label flipped | 9/17 (53%) |
| Two gap labels flipped | 8/17 (47%) |

Only two flipped labels, or counting the recorded-in-unit claims against
the judge, take it under the bar; the second treats them unlike the hidden
positives they resemble.

## Conclusion

All four bars are met, so `kmctl decision candidates` and its skill are worth
building. Precision clears its bar at the point estimate; its interval runs
from 36% to 78% and two flipped labels would put it under, so a person reviews every claim, as the skill's
report-first design already requires. The recall is a floor for the real
skill, which can read the full diff the judge never saw, and may sit a
little high from the record-keeping words the hiding left.

What to build with:

- **Judge every unit; use the filter only to order the report.** Judging
  costs about two cents a unit, so the whole of this range costs less than
  cutting at score 2, which would lose 5 of 30 decisions.
- **Show the judge the unit's own `.okf/decisions/` changes.** Half of the
  claims on other units were choices the unit recorded as an amendment; a
  real run that sees them answers `covered`.
- **Give it the plan's intent** when the ticket has one, and the decision
  index as it stood before the unit.
- **Tell it features and interface details are not decisions**, with the
  false alarms above as examples, to cut the seven false alarms.
- **Report record-only units apart**: a unit that only writes a record
  points at a choice made elsewhere.
