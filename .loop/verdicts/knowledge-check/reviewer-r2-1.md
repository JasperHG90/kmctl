---
type: verdict
title: 'Verdict: knowledge-check reviewer round 2'
description: 'reviewer verdict for round 2 of knowledge-check: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:41:21+00:00'
slug: knowledge-check
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All six round-1 findings are fixed, each with a test that fails without the fix, and the gates are green. The fence fix is incomplete for nested fences (f7), which still gives a false failure on an index that shows a fenced markdown example. That and two small items are plain fixes, so the label is fix.

## Checked

- Read src/kmctl/checks.py, tests/test_check.py, tests/test_help.py and the check verb in src/kmctl/__init__.py in full.
- Ran `loopctl gate stamp` in the worktree: lint, format and tests pass, eval rows r1 to r6 pass, "stamp green: 4d13ec08deff784f6c8690323c9ce91a815180e69cd24aca5e96f35f0dbb469b".
- Rows r1 to r6: the tests are unchanged from round 1 and still assert each row's fails_when. The fixes did not weaken them.
- Checked that each new test fails without its fix: the fence and out-of-folder tests link files that do not exist, and the hidden-pages test adds files the old rglob would report.
- Probed in a scratch repo: a ```` fence holding a ``` example (false failure, f7), a non-UTF-8 root index (extra unlinked-section findings, f8), and a non-UTF-8 section index (one finding, exit 1). Ran `kmctl check` on this repo: pass.

## Findings

- f1 resolved: single fences are skipped. The nested case is f7.
- f2 resolved: out-of-folder links are no longer entries.
- f3 resolved: one hidden rule now applies to docs/, sections and prototypes.
- f4 resolved: a non-UTF-8 index is a finding, not a traceback.
- f5 resolved: the docstrings and types asked for are in place.
- f6 resolved: help tests exist for every verb.
- f7 open, non-blocking: nested fences flip the fence state, so the false failure f1 named still happens for a fenced markdown example.
- f8 open, non-blocking: an unreadable root index also reports every section as unlinked.
- f9 open, non-blocking: _read has no docstring.
