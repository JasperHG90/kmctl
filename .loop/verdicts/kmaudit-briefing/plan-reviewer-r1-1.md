---
type: verdict
title: 'Verdict: kmaudit-briefing plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-briefing: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T14:02:37+00:00'
slug: kmaudit-briefing
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works and the one listed risk (speed) is settled by spike 1. But the plan's central promise, read-only, rests on readers that write. In this repository the only store is the legacy `.kmctl/audit.sqlite` at an older schema, so the obvious build copies and migrates it on first run. The plan needs to say how it reads stores without `Store` (p1). It also needs to stop promising that pending matches `claims list`, which contradicts r2 and r3 (p2). Both are revisions, not a rethink. No split needed.

## Checked

- Spike kmaudit-briefing/1: README, stdout, stderr. The timings answer the speed risk (0.03s cut and compare for 212 sections, 0.06s check counts). The 212-pending result confirms the `previous_keys` trap, which the plan now covers. The 0.51s first open was `Store` copying the legacy store, which is a write.
- `store.py`: `Store.__init__` (mkdir, .gitignore, `_copy` of the legacy store, `_migrate`, meta insert), `refresh` (the `previous_keys` re-key path), `extracted`, `documents`.
- `namespaces.py`: `listing` and `_count` already read with `mode=ro` and fall back to `LEGACY_STORE`. That is the pattern the briefing needs.
- `check_verbs.list_checks` and `status_row`, `verbs.list_claims`: all open `Store`.
- This repository's state: no `.kmaudit/`. `.kmctl/audit.sqlite` is at user_version 5 in WAL mode with no `meta` table. A `mode=ro` open leaves the main file's bytes alone but creates empty `-shm`/`-wal` sidecars. I removed the ones my probe made, after checking no process held the file.
- 2.0 facts: O1 and O2 match the prose. O2 is support, needs O1, and could not ship alone. Its fixes and touches line up with the prose.

## Findings

- p1: read-only is a premise the reused code does not meet. On this repo the legacy store at schema 5 would be copied and migrated.
- p2: pending cannot match `claims list` when pages changed or keys came from a previous hash, so r1 contradicts r2 and r3.

## Notes

The status list in the prose leaves out `no check` and `skipped`, which `list_checks` can return. r1's count comparison will catch that during the build, so it is not a finding.
