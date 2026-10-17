---
type: verdict
title: 'Verdict: harness-prompt-reviewer-f1 reviewer round 1'
description: 'reviewer verdict for round 1 of harness-prompt-reviewer-f1: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:21:30+00:00'
slug: harness-prompt-reviewer-f1
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `_read_answer` now reads a word as a number only when `word.isdecimal()`, so `²` or `①` falls through as a name, `parse_harnesses` rejects it, and the prompt loop asks again with the accepted values. Every value that passes `isdecimal()` also parses with `int()`, so no ValueError path is left.

## Checked

- Diff against HEAD (the change is uncommitted in the worktree): one line in src/kmctl/__init__.py:777 and one new parametrized test at the end of tests/test_plugin.py.
- Row r1: `test_prompt_non_decimal_digit_is_asked_again` types `²` (and `①`), then `1`. It asserts exit code 0, no exception, that install ran for `["claude"]`, and that stderr has "one of: 1 claude, 2 antigravity". On the old `isdigit()` code, `int('²')` raises ValueError, so exit code and exception assertions fail. The row's fails_when is covered. I confirmed `'²'.isdigit()` and `'①'.isdigit()` are True and `isdecimal()` is False for both.
- Row r2: full suite plus integration.
- `loopctl gate stamp` from the worktree: lint, format, tests, integration, r1 and r2 all pass; "stamp green: d5a7e087d6d94a495e8822440404b88490dbfa87d6d0c43bea881f3ee7f080c4".
- Consistency: the `_read_answer` docstring ("by number or name; raises PluginError otherwise") still holds. No other `isdigit` use in src, tests or docs.

## Findings

None.
