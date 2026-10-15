---
type: verdict
title: 'Verdict: audit-hermes-hardening reviewer round 2'
description: 'reviewer verdict for round 2 of audit-hermes-hardening: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T16:14:16+00:00'
slug: audit-hermes-hardening
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed. `add` now writes the merged list with every backtick escaped as
`. In valid JSON a backtick can only sit inside a string, so the escape
always gives valid JSON that decodes to the same text, and a finding can no
longer close the fence early. The gates are green. Nothing else changed in a
way that needs another look, so the label is pass.

## Checked

- Read the fix at action/audit-batches.py:85-88: `json.dumps(earlier + new, indent=2).replace("`", "\\u0060")`.
- Reran my round 1 repro with the round 1 inputs: the first add passes, and the second add, which used to fail with "Unterminated string", now passes too. The merged file has exactly one fence pair.
- Ran audit-report.py on that merged file: it exits 0, and the summary row shows "use ``` fences" with real backticks, because json.loads decodes the escape.
- Read tests/test_ci_audit.py::test_merged_block_survives_backticks. It merges two replies whose summaries hold ``` and `code`, escaped the way a model would escape them. It checks there is one fence pair (three parts after splitting on ```) and that the second finding's summary parses back to the original text. Without the escape the fence count would fail, so the test asserts the behaviour.
- Ran `loopctl gate stamp` from the worktree: lint, format, tests and rows r1, r2, r3, r5, r4 all pass. It ends "stamp green: 28bf47f02158a3208359b7b399a8ff2a8385151dfb88a861960b79a840dade2c".

## Findings

- f1 (resolved): fixed at action/audit-batches.py:87 and covered by test_merged_block_survives_backticks. Repro and render checked as above.
