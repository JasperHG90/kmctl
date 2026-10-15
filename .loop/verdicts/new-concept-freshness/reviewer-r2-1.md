---
type: verdict
title: 'Verdict: new-concept-freshness reviewer round 2'
description: 'reviewer verdict for round 2 of new-concept-freshness: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T19:08:40+00:00'
slug: new-concept-freshness
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both findings sent back are fixed and the fixes broke nothing nearby. The
change can be committed.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass; rows r1 to r6 pass; "stamp green: 0b433448b538bd9e184e94abf4fb9eaa3691f622e20ae24aff5659cc3e8fee5d".
- Ran the round 1 edge script again against the worktree. The 5000-digit count is now refused with the --stale-after message instead of crashing, and `٣d` is refused. Every other case gives the same result as in round 1.
- Six-digit cap: `100y` gives 2126-10-15, `999y` and `999999d` are accepted, and `7973y` reaches 9999-10-15. `7974y`, `999999w`, `999999m` and `999999y` are refused as too far in the future. `1000000d` is refused as not a duration. Every count the plan has in mind (days to a few years) fits easily, and anything the cap cuts off is past year 9999 anyway in every unit except days, where it is past year 4764.
- test_stale_after_refused_odd_counts asserts a ConceptError naming --stale-after for the 5000-digit count, the Arabic-Indic digit and a seven-digit count. It would fail if any of them crashed or were accepted.
- The r4 command now runs test_new_freshness_valid by node id plus tests/test_okf_fields.py. The r5 command runs test_init_block_names_freshness and test_new_freshness_documented by node id. Both pass in the stamp.

## Findings

- f1: resolved. `_DURATION` is `([0-9]{1,6})([dwmy])` at src/kmctl/concepts.py:51, and the comment above it says why.
- f2: resolved. The r4 and r5 commands in rows.json name their tests by node id.
