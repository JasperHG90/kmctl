---
type: verdict
title: 'Verdict: decision-gaps-measure plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of decision-gaps-measure: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T11:49:52+00:00'
slug: decision-gaps-measure
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach can work and the range and positives are real: the draft units.py gives 161 units, 31 of them adding ADRs 0010 to 0045. But the hiding leaves a strong shape leak (.okf/log.md is touched by every positive but only a quarter of negatives), the cited spike cannot detect leaks because it checks with the same regex it strips with, record-only positives skew recall, and the plan sets no sample size or bar for the verdict. Each needs a revised plan, not a rethink.

## Checked

- Read the plan, rows.json and spike 1 (README, stdout, run.json), plus the draft units.py, hide.py and leak_check.py in the scratchpad.
- Reran the draft over units.jsonl: counted how often positives and negatives touch .okf/log.md, index.md and summary.md, and counted the files each positive changes outside .okf/ and .loop/.
- Scanned the stripped positive texts with a word list separate from LEAK (chose, choice, rejected, record, four-digit numbers). 21 of 31 hit something. Most hits are the operator's choice, which a real gap's plan would also carry and so is fair signal. The 0013 and 0030 hits are real tells.
- Negatives that hold real gaps: the plan handles this. Judge claims on negatives are read and labelled, and precision counts a correct claim as correct. The false-alarm rate is then an upper bound, which the README should say.
- Problems, Goals and Outcomes: one problem, one goal, one behaviour outcome. All match the prose. The touches cover the scripts, the README, the indexes and the test file named by the rows.

## Findings

- p1: the bookkeeping shape leak in the diff stat and the leftover number and summary tells.
- p2: the spike's leak check is tautological, so the risk is still open. A second spike should answer it.
- p3: record-only positives need their own rule for recall and for labelling the unit that made the choice.
- p4: no negative sample size and no bar for the build verdict.

## Notes

- Judge stand-in: claude -p with no tools, seeing only the message, stat, intent and earlier decisions, is a fair lower bound but not the skill itself. The real skill runs as an agent that can read the full diff. The README should present the judge's numbers as a floor. Whether claude -p, run from the checkout with settings turned off, still loads CLAUDE.md or the SessionStart briefing (which would hand it later decisions) can be answered by running it. The simplest fix is to run the judge from an empty temporary directory.
- One ticket is enough. The four findings are all about measurement design inside one prototype, not separate risks that call for a split.
