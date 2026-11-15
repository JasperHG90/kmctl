---
type: verdict
title: 'Verdict: kmaudit-namespaces-nested-store reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-namespaces-nested-store: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:23:48+00:00'
slug: kmaudit-namespaces-nested-store
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change fixes the bug the plan names. One helper, `namespaces.read_only_uri`, builds the read-only URI from `Path.resolve().as_uri()`. All three hand-built `file:` URIs (`namespaces._count`, `briefing._read_only`, `store._copy`) now use it, and no other one is left in `packages/`. Each eval row's test fails when its behaviour is broken. The gates are green. Nothing blocks the commit.

## Checked

- Diff against agent-audit (uncommitted in the worktree): briefing.py, namespaces.py, store.py, test_briefing.py, test_namespaces.py. I read every changed function and its callers. `grep` for `mode=ro`, `uri=True` and `file:` in non-test code under `packages/` finds only the helper and its three call sites.
- Behaviour: `_count` still opens outside its try, so a store that cannot be opened still raises, while a missing table still counts as 0, as the plan asks. `as_uri` needs an absolute path, and `resolve()` handles relative paths. store.py and briefing.py already imported `namespaces`, so the change adds no import cycle.
- Gates: I ran `loopctl gate stamp` in the worktree myself. lint, format, tests and integration pass, as do eval rows r1, r2 and r3. `stamp green: c305c192988b9ce1443324f7965c3b97aecaa9d6dbe731b5ded3fb9288742508`.
- Mutation checks, run on a copy of the tree in my scratch directory, with the real stores never touched:
  - With the helper reverted to `f"file:{path}?mode=ro"`, all 8 new tests fail. That covers r1 (nested namespace listed with sections == 2), r2 (`handbook/guides` missing from the briefing) and r3 (the four URI-character paths, the relative path, and the legacy copy).
  - With only `store._copy` reverted, the legacy-copy test still fails, so r3 covers the copy on its own.
  - With only `briefing._read_only` reverted, the r2 test still fails, so r2 covers briefing on its own.
- Docs: `.okf/` and `docs/` say nothing about the URI form or `%2F`. The new docstrings are accurate.

## Findings

None.

## Notes

The two `read_only_uri` tests import the helper inside the test function rather than at the top of the module. This is a style point and asks for nothing. The r3 command also selects from test_claims_store.py, which has no `uri` tests. The row still works through test_namespaces.py.
