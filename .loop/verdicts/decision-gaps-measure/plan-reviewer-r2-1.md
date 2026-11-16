---
type: verdict
title: 'Verdict: decision-gaps-measure plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of decision-gaps-measure: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T11:53:57+00:00'
slug: decision-gaps-measure
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

All four round 1 findings are resolved. The hiding now treats every unit alike, an independent spike puts the visible paths at chance and names a small word residue, record-only positives are counted apart, and the build bars are fixed before the judge runs, over the whole range. I found no new risk that would break the plan. Problems, Goals and Outcomes match the prose.

## Checked

- Read the revised plan, the re-signed rows.json, spike 2 (README, stdout, run.json, stderr), and the round 1 verdict.
- Read the draft hide.py, signals.py, judge.py and leak_spike.py. visible_files drops `^\.(okf|loop)/` for every unit. signals.py and judge.py read only visible_files and strip output. leak_spike.py's word list (record, cites, number, index, log, summary, bundle, written, entry) does not overlap LEAK, so spike 2 can fail, unlike spike 1.
- Reran the counts on results/units.jsonl: 161 units, 31 positives. Only ADR 0030's unit has 0 visible files, which matches 30 counted positives and 130 negatives in the plan and in spike 2's stdout.
- Bars against the sample: 21 of 30 is 70%, with a Wilson lower end of about 52%, so the two recall bars agree and can be met. The two trial judge runs in results/try_judge.jsonl cost $0.02 to $0.04 per unit, about $3 to $6 for the range, so the cost bar is reachable and the claude -p flags (no tools, no settings, empty cwd) run.
- Index leak: judge.py reads the decision index at the unit's first parent, which does not yet list the unit's own ADR.
- Plan presence: 27 of 31 positives and 82 of 130 negatives have a plan intent. That is a real feature a true gap would share, not a trace of the hidden record.
- 2.0 facts: one problem (P1), one goal (G1), one behaviour outcome (O1) that can ship alone, needs none. Touches cover the README, scripts, indexes and test named by the rows. I found no outcome missing from the prose and no prose behaviour without an outcome.

## Findings

- p1: resolved. Bookkeeping paths are hidden from every unit and the strip pattern is wider.
- p2: resolved. Spike 2 uses independent detectors and settles the risk, with the 0.64 word residue named.
- p3: resolved. Record-only positives (ADR 0030) are reported apart and out of recall.
- p4: resolved. The judge runs on the whole range, and the bars are fixed before it runs.

## Notes

- The plan does not say whether a judge "missing" on a positive counts as a hit only when its stated choice matches the hidden ADR. In practice the precision bar on negatives keeps an over-eager judge in check, and the stripped intent of these tickets is mostly the decision itself. Still, score.py should check the match (or label positive hits as negative claims are labelled) so that "recall" means the judge found the decision in that unit.
- The touches name scripts/leak_check.py, the script that could not fail. The README's 0.64 residue should come from spike 2's leak_spike.py logic under whatever name lands in the folder.
- The prose says ADRs 0036 to 0045 arrived "inside #53", but units.jsonl spreads them over five units (0036-0041, 0042, 0043, 0044, 0045). The count of 31 stays right.
