---
type: verdict
title: 'Verdict: verify-folder-and-path-ids reviewer round 2'
description: 'reviewer verdict for round 2 of verify-folder-and-path-ids: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-27T10:22:53+00:00'
slug: verify-folder-and-path-ids
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

The fix closes f1. An id that starts with `.okf/` now always resolves under
`.okf/`, so `.okf/docs/how-to/run.md` is refused and no file changes. The
nearby spellings still work, and the r4 test now covers this case. Nothing
else blocks.

## Checked

- Gates: I re-ran `loopctl gate stamp` from the worktree. Lint, tests,
  integration and rows r1 to r6 all passed: "stamp green:
  f6558b8d9250678e12e282d4b8d86564c2bbc0e29cb9d6000fb07246583fbd75".
- Code: I read `_targets` in `packages/kmctl/src/kmctl/verify.py` (lines
  106-139). `in_okf` is set before the prefix is stripped, and `docs` now
  requires `not in_okf`. Base, shown path, canonical id and the `_pages` set
  then all point at `.okf/`. The canonical check still compares against the
  stripped id, so `.okf/decisions/0001-a.md` stays accepted. The docstring
  still holds.
- Test: `test_verify_refuses_a_file_review_due_never_lists` gained
  `.okf/docs/how-to/run.md`. A real `docs/how-to/run.md` is present in its
  fixture, and the test asserts exit 1, one refusal line on stderr, and no
  file changed. That is what f1 needs.
- Probes in a scratch repo with `--by human:t`: `.okf/docs/how-to/run.md` was
  refused with "no concept, docs page or folder ... at
  .okf/docs/how-to/run(.md)", and the tree stayed clean. `docs/how-to/run`,
  `docs/how-to/run.md` and `.okf/decisions/0001-a.md` each still verified the
  right file.

## Findings

- f1: resolved. `packages/kmctl/src/kmctl/verify.py:107-109` (the `in_okf`
  flag) fixes it, and the r4 parametrized case covers it.
