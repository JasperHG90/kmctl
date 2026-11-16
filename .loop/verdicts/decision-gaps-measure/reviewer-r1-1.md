---
type: verdict
title: 'Verdict: decision-gaps-measure reviewer round 1'
description: 'reviewer verdict for round 1 of decision-gaps-measure: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T14:09:17+00:00'
slug: decision-gaps-measure
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The prototype does what the plan asks. Hiding is applied to every unit the same way. score.py computes the README's numbers and the bars the plan set, and the scripts rerun to the committed results. The build verdict holds under every reading of the labels that treats claims on negatives the same way as hits on positives. The findings are about wording. The headline "9 of 17 claims" misstates the claim count (f1). The README should also say that precision clears its bar by one label, and what the excluded and double-counted claims do to it (f2). None of them blocks.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2 and r3 all pass, "stamp green: 52b53f080376578254041b938004ed79f7ba1d0940eca7c051ffbfeb0ce4cdf4".
- Ran score.py over results/: it prints exactly the README's filter table, recall 25/30 (Wilson 66% to 93%), misses 0019/0031/0033/0034/0042, 32/130 claims (9 gap, 8 false alarm, 15 recorded in unit), precision 9/17 (Wilson 31% to 74%), $3.19, and "verdict: build". Ran leak_check.py: AUC 0.64 for words and 0.50 for paths, as the README says. `okf_validate.py .okf --strict` reports the bundle conformant, and `kmctl check` reports all checks passed.
- Hiding: judge.py, signals.py and leak_check.py all take the files from `hide.visible_files` and the subject, body and plan intent from `hide.strip`, the same for every unit. The plan intent comes from today's plan for positives and negatives alike, and the index is taken at the first parent. Nothing branches on `adds_decisions` before scoring, except leak_check's record-only skip, which the plan asks for.
- score.py: record_only means a unit with no path outside .okf/ or .loop/, which matches the plan. Recall needs both a `missing` verdict and `matches_hidden_decision`. Precision is gap / (gap + false_alarm). It asserts that every unit has a judge result and every claim a label. The Wilson formula is correct.
- Positives: compared each judge `choice` with the hidden ADR's title for all 25 hits. All 25 match. The 0036 to 0041 unit's choice matches 0041.
- Negatives: read all 32 claims, using the judge's choice and rejected option, the unit's subject, its visible files and its .okf/decisions changes. All 15 recorded-in-unit units do change an existing ADR. I read the amendments in a4c175d9, 05881e5e, 14b6616f, 1e33636c and 3d88e355, and each records the claimed choice. Checked the decision index at the parent of each gap unit: no gap was covered by an earlier ADR.
- My disagreements with the labels: 3b1acae3 (vendoring the okf validator rather than depending on okf-skills) is a dependency choice with a rejected option, and the judge's own instructions name dependencies, so I would call it a gap, not a false alarm. c92c6e0d (a collector job instead of changing the ruleset) and b49e8332 (toiminnot actions) are borderline, but the repository recorded a similar toiminnot adoption as ADR 0035, so I keep both as gaps. The two MIT units are one change counted twice. With my labels and MIT counted once, precision is 9/16 (56%). Under the plan's own rule, where a correct claim counts as a hit and recorded-in-unit claims are correct claims, it is 24/32 (75%) or higher. Only counting recorded-in-unit claims as false alarms would flip the verdict, and that would treat them differently from the hidden positives they resemble. So no disagreement of mine flips the verdict, but the margin is one label.
- Tests: test_units_and_signals_reproduce_the_committed_results compares the rerun output byte for byte with the committed files. r1's `-m 'not llm'` overrides addopts' `not integration`, so it runs. The README tests compare score.py's output with the README text, and r2's `-k judge` selects both judge tests, which fail when a unit lacks a judge result or a claim lacks a label, through score.py's asserts. test_repo_apm's exclusion of the results files is justified: units.jsonl and judge.jsonl name aim from the history before the APM switch.

## Findings

- f1: the description, the index line and the log line say "9 of its 17 claims elsewhere", but the judge made 32 claims on the 130 negatives. Say "9 of the 17 claims that were not recorded in the unit", or give 32 first.
- f2: the README should state that precision is gap / (gap + false alarm), with the 15 recorded-in-unit claims set aside, a category the plan did not name. It should say that under the plan's rule those claims are correct and precision would be 24/32. It should say that MIT is one change counted as two gaps (8/16 once deduplicated) and that one flipped label puts precision under 50%. Then the operator reads the build verdict with its real margin.
- f3: leak_check.py's docstring names a script that is not there.
- f4: the signals.py and judge.py docstrings describe narrower hiding than the code does.
- f5: the "mostly summary and bundle" breakdown has no script behind it. Print it from leak_check.py or drop it.
- f6: r3's command does not run strict OKF validation. A test that runs tests/vendor/okf/okf_validate.py on .okf --strict would close that. The pre-commit hook covers it for now.

## Notes

- The positive labels carry only a boolean. A one-line note per hit, as the claims have, would let the operator audit them without rerunning my comparison.
