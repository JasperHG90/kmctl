---
type: verdict
title: 'Verdict: decision-gaps-measure reviewer round 2'
description: 'reviewer verdict for round 2 of decision-gaps-measure: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T14:52:28+00:00'
slug: decision-gaps-measure
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All six round 1 findings are fixed. The relabel left one stale number behind: the Conclusion still says "eight false alarms" where the Results now say seven (f7). It is a one-word fix that does not need another look.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2 and r3 all pass. Output: "stamp green: cdfa89cdf90d4d9c1b8d7a417065977afd549dd474b92ba29bf48936d957affb", the fingerprint this round is bound to. r3 now runs `okf_validate.py .okf --strict` too.
- Ran score.py: it prints 32 claims (10 gap, 7 false alarm, 15 recorded in the unit), precision 10/17 (59%, Wilson 36% to 78%), and the five other readings (9/16, 25/32, 10/32, 9/17, 8/17). These match the README table line for line, and the verdict is still build. The `same_change` reading uses labels.json's new `same_change` list of the two MIT units.
- labels.json: 3b1acae3 is now `gap`, with a note saying it was relabelled after review.
- Ran leak_check.py: AUC 0.64 for words and 0.50 for paths, and it prints the per-word rates. "entry", "bundle" and "summary" lead, as the README says. The usage line names leak_check.py itself.
- The signals.py and judge.py docstrings now say every path under .okf/ and .loop/ is dropped for every unit, which matches hide.visible_files.
- README description, prototypes index line and log line all say 32 claims, 15 recorded in the unit, and 10 of the other 17 gaps.
- Did not run judge.py.

## Findings

- f1 resolved: the description, the index and the log now give 32 claims first, then 15 recorded in the unit and 10 of 17.
- f2 resolved: the README defines precision, says the recorded-in-unit category was added after the run, and has a table of the other readings from score.py with the thin-margin caveat. The Conclusion repeats the interval and the two-flip point.
- f3 resolved: leak_check.py's usage line names itself.
- f4 resolved: both docstrings describe hiding .okf/ and .loop/ for every unit.
- f5 resolved: leak_check.py prints the per-word breakdown the README cites.
- f6 resolved: r3 runs the strict validator, and the stamp shows it passing.
- f7 open (docs, non-blocking): README.md line 149 says "to cut the eight false alarms". The count is seven since 3b1acae3 became a gap. Change it to seven.
