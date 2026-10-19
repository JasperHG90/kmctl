---
type: verdict
title: 'Verdict: review-due-commit-order reviewer round 1'
description: 'reviewer verdict for round 1 of review-due-commit-order: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:44:17+00:00'
slug: review-due-commit-order
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The commit-order approach is sound and matches the plan: the verification commit, the source-changed diff from it and the new edited-after-verification reason all behave as the plan says, the tests assert each row, and the docs and ADRs agree. One crash blocks: `_show` misreads git cat-file's "missing" line when the path has a space, so `kmctl review due` raises ValueError for a verified file with a space in its path that was once deleted from history (f1). A small docs gap in the repo's own rule copy is non-blocking (f2).

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r7 all pass; "stamp green: 888e493c2ed528a1d6ce04923414c48c269f37d05a046d0eed87384d2c3ff85d".
- Read src/kmctl/review_due.py in full and the diffs of okf.py, kinds.py, __init__.py, test_apm_package.py and test_review_due.py. Checked the `git log --cc --name-only -z --relative --format=@%H` output shape with od: the "\0\n" after each header is handled by the lstrip, so the parse is right.
- Rows: r1 lands by squash, rebase plus fast-forward and --no-ff merge, with a source change before the verification on the branch (issue #17), and asserts an empty list. r2 makes a source change after landing with an earlier commit date and asserts the exact reason. r3 covers a body edit and a description edit and asserts the exact reason. r4 covers a verify-only commit with and without stale_after, plus an uncommitted entry and an entry never committed. r5 runs the same cases for a docs page, including the unverified baseline with dates in reverse order. r6 checks verification_commits against a separate per-file git log reference across a merge commit, a conflict-resolution merge, a rename and a double verify, and asserts that every reference value is set. None of these is vacuous.
- r8 (judgment): ADR 0032 exists and names the reason `edited after verification`. ADR 0006 and ADR 0023 each have a `## Correction, 2026-10-19` linking to it. The module docstring, the review due and verify help, docs/reference/commands.md, both docs-layout package copies and the kinds.py sources description all describe commit order. A grep finds no remaining date-based description except f2. Pass, apart from f2.
- By hand: a delete-then-restore of a verified page without a space in its path works (the missing spec gives None, and a later edit lists `edited after verification`). The same history with a space in the path crashes (f1). `kmctl review due` on this repository took 0.39 s in the worktree, against 0.56 s on main in the plan.

## Findings

- f1: in `_show`, `header = data[i:nl].split()` followed by `len(header) != 3` treats "abc:./docs/how/my page.md missing" as a found object, and `int(header[2])` raises. Check whether the line ends in "missing" (or rsplit the header from the right) and add a test with a spaced path deleted in history.
- f2: .claude/rules/docs-layout.md line 84 keeps the old wording. The package copy changed and this kmctl-specific copy did not.

## Notes

The accepted loss (a verification and a source change folded into one squash commit) and the cherry-pick difference between the batched and per-file walks are both written down in ADR 0032's Consequences. The plan leaves the hash alternative to the operator.
