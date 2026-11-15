---
type: verdict
title: 'Verdict: kmaudit-namespaces-nested-store plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-namespaces-nested-store: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:03:45+00:00'
slug: kmaudit-namespaces-nested-store
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan lists no risks, and I found none that could break it. The fix works as described.

## Checked

- The three call sites are as named: namespaces.py:89 (`_count`), briefing.py:68 (`_read_only`), store.py:170 (`_copy`). All build `file:{path}?mode=ro` by hand, so the `%2F` in a nested store's name is decoded by SQLite. That is the cause the plan names.
- I checked the approach in a scratch dir on Python 3.12.16: `Path.as_uri() + "?mode=ro"` on a store named `packages%2Fkmaudit.sqlite`, under a folder named `r%x#y?z`, opens and reads with `uri=True`. `%` turns into `%25`, `#` into `%23`, `?` into `%3F`.
- The 2.0 facts match the prose. There is one cause (hand-built URI) at three sites, it is one problem, and O1 ships alone. Its `touches` cover the three modules and their tests.

## Findings

None.

## Notes

`Path.as_uri()` raises ValueError on a relative path. Every production root comes from `namespaces.repository_root`, which resolves, and the tests use `tmp_path`. So this cannot break the plan. The helper can still call `.resolve()` or `.absolute()` first, since `Store(root)` takes any path.
