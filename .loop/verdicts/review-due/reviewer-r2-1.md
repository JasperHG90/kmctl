---
type: verdict
title: 'Verdict: review-due reviewer round 2'
description: 'reviewer verdict for round 2 of review-due: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:49:29+00:00'
slug: review-due
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All four round-1 findings are fixed, and each fix has a test that fails without it. The `>=` change in the shared `has_passed` keeps review-due and handoffs consistent: a handoff at its exact stale_after instant is now expired in both, and the handoffs docstring ("has not passed") still reads true. One non-blocking docs finding is left: the help text does not mention folders.

## Checked

- Ran `loopctl gate stamp` in the worktree: lint, format, tests and eval rows r1 to r7 all pass, "stamp green: 58eb8bdae514...".
- Read the round's changes in src/kmctl/review_due.py, src/kmctl/okf.py, tests/test_review_due.py and tests/test_handoffs.py, and how handoffs.py uses has_passed.
- In a scratch copy, I reverted the `-z` split and the folder check one at a time, with PYTHONPATH pointing at the copy. test_due_source_with_non_ascii_name and test_due_source_folder then both fail, so they test the fixes. core.quotePath is not set globally, so the café test runs with git's default quoting.
- test_has_passed_at_the_exact_instant asserts True at the same instant and False one second earlier, which fails under the old `<`.
- r7 now asserts `data["due"] == ["new"]` and both exit codes are 0. The `_git` strip() leaves NUL separators intact. The folder check skips the repository root (empty rel), so `.` still gives a notice.

## Findings

- f1 resolved: `ls-files -z` split on NUL at review_due.py:158-159, covered by test_due_source_with_non_ascii_name.
- f2 resolved: okf.py has_passed uses `now >= when`, and its docstring cites §5.5. Covered in tests/test_handoffs.py.
- f3 resolved: `_resolve` accepts a path with a tracked file under it, covered by test_due_source_folder.
- f4 resolved: test_exit_and_json asserts the due list and the --json exit code.
- f5 (non-blocking): a one-line help text change. A plain fix is enough, so it does not need to come back to me.
