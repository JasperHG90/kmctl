---
type: verdict
title: 'Verdict: kmaudit-briefing plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmaudit-briefing: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T14:05:06+00:00'
slug: kmaudit-briefing
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Round 1's two findings are fixed. The briefing no longer opens `Store`, and pending is now the briefing's own count. One new premise breaks the plan as written: SQLite's `mode=ro` on a WAL database creates `-shm` and `-wal` sidecar files and leaves them behind, so the plan's chosen read path fails its own "no file appears" acceptance and eval r2 (p3). That needs a revision, not a rethink. No split needed.

## Checked

- Plan and signed eval r1 to r4, round 1's verdict, spike kmaudit-briefing/1 (README, command, outcome).
- p1: `Store.__init__` still mkdirs, writes `.gitignore`, copies, migrates and inserts into `meta`. The plan now avoids it. `status_row`, `check_store.check`, `feedback.latest`, `feedback.current`, `_reason_status`, `_status` and `Repository` (git ls-files, sha256 of the working tree) only read, so `status_row` over a `Store` built without its constructor works. The legacy store is at user_version 5, which has every table those readers use except `meta`, which they do not touch. So the acceptance case can produce statuses.
- `list_checks` is `status_row` over `_checkable(store, target)`, so statuses match `checks list` as long as the briefing uses the same claim set.
- p2: r1 now requires only sections, claims, statuses and open feedback to match the list commands, and pending to match a fresh cut. That matches the prose.
- p3: ran SQLite on a scratch copy of the real store (header bytes 18 and 19 are 2, so WAL; user_version 5; 207 sections). A `mode=ro` open created `audit.sqlite-shm` and `audit.sqlite-wal`, and both stayed after close. `mode=ro&immutable=1` read the same counts and created nothing. A synthetic WAL store did the same. I did not open the operator's real store.
- 2.0 facts: O1 (behaviour, fixes P1) and O2 (support, needs O1, fixes P2) match the prose. O2 cannot ship without the verb. Touches cover briefing.py, cli.py, the tests, commands.md and the README.

## Findings

- p1 resolved: the plan reads store files itself and builds a read-only handle for `status_row`.
- p2 resolved: pending is now the briefing's own count, and eval r1 says so.
- p3 open: `mode=ro` is not file-silent on WAL stores. The prose names `mode=ro` and copies `listing`, which has the same side effect (round 1's probe of `listing`'s pattern is what left sidecars in the operator's `.kmctl/`). A test that builds a store with `Store`, closes it (the sidecars go away when the last writer closes), then runs the briefing will see new files and fail r2. The plan should name a sidecar-free open, such as `immutable=1`, and accept its cost: it ignores a non-empty `-wal` left by a running or crashed writer, so counts can lag. Or it should reword r2 and the acceptance to allow SQLite's sidecars. Either way it is a choice about the contract, which is why it belongs in the plan and not the build.

## Notes

`namespaces.listing` and `_count` have the same sidecar side effect today. If the plan picks `immutable=1`, using it there too would keep `kmaudit namespaces` file-silent, but that is outside this ticket unless the operator wants it.
