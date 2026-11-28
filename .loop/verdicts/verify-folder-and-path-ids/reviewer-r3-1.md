---
type: verdict
title: 'Verdict: verify-folder-and-path-ids reviewer round 3'
description: 'reviewer verdict for round 3 of verify-folder-and-path-ids: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-27T10:32:38+00:00'
slug: verify-folder-and-path-ids
pass: reviewer
round: 3
body_schema: verdict/1
---

## Summary

The committed tree (fe7fb6e0) is the change rounds 1 and 2 reviewed, now with
its new files tracked. The f1 fix is in, nothing stray came along, and the
gates are green at the committed fingerprint. Pass.

## Checked

- Gates: I re-ran `loopctl gate stamp` from the worktree on a clean tree.
  Lint, format, tests, integration and rows r1 to r6 all passed: "stamp green:
  b43e5b4cd37e61acdbfc55419062852a5a05b85f73790365092818e73f88847b".
- Diff: `git diff main...HEAD` touches 15 files, all ones round 1 and 2
  covered: `pages.py`, `verify.py`, `review_due.py`, `__init__.py`, the two
  test files, ADR 0059, the ADR 0055 correction, `decisions/index.md`,
  `log.md`, `docs/reference/commands.md` and both okf-bundle instructions.
  The newly tracked `pages.py` and ADR 0059 are the files the round 1 verdict
  already read.
- The `.okf/.acks` change deletes the 2026-11-26 ack and adds one against
  ADR 0055. That is what `kmctl summary ack` does itself, since it removes the
  old ack when it writes a new one (`summary.py:340`). The new ack is needed
  because ADR 0055 got a dated correction. It is not stray.
- f1: `_targets` in `verify.py` sets `in_okf` before it strips `.okf/`, and
  `docs` requires `not in_okf`. The r4 test still lists
  `.okf/docs/how-to/run.md` (`test_verify.py:638`).

## Findings

- f1: resolved. The `in_okf` flag at `packages/kmctl/src/kmctl/verify.py:107-109`
  is in the committed tree, and the r4 case covers it.
