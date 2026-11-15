---
type: verdict
title: 'Verdict: kmaudit-briefing reviewer round 2'
description: 'reviewer verdict for round 2 of kmaudit-briefing: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T14:27:44+00:00'
slug: kmaudit-briefing
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three findings from round 1 are fixed. A store at any older schema step now briefs like a current one, and the file stays unchanged. The --json output and the docs now agree in the empty and error cases. No new problems came in with the fixes, so the verdict is pass.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r4 all pass, "stamp green: 9c713bd4a8b1da46b16d1b324af4bebd61787597262fc41bf9640b90ef86291b".
- Read `briefing._read_only` alongside `Store.__init__` and `Store._migrate`. The source opens with `mode=ro` and closes after the backup. `_migrate` touches only `self.db`, so a `Store` built with `object.__new__` that has `path` and `db` set is enough for the readers it calls (`extracted`, `claims`, `status_row`, `latest`). Every migration step runs on the in-memory copy only.
- Ran my round 1 script (old_step.py) with the worktree's package at steps 1 to 6. In round 1, steps 1, 2 and 4 raised OperationalError. Now all six brief the same: 4 sections (3 pending), 1 claim, "1 no check".
- Real data: I copied the operator's .kmctl/audit.sqlite into a scratch git repo with this tree's .okf and never opened the original. The briefing printed exactly what it printed in round 1 (207 sections, 25 pending, 1281 claims, 1 open note, and the same check counts) in 0.19s. The copy's sha256 did not change, and no .kmaudit/ appeared.
- Test for f1: `test_a_store_at_an_older_schema_step_still_briefs` rebuilds the store from `STEPS[:step]` while keeping sections, extractions and claims. It asserts that the file's bytes are unchanged, that sections, claims and pending match the current store, and that checks equal {"no check": 2}. On old code, steps before 5 would raise and the CLI would print 'unavailable', so `briefing()` would fail at json.loads or the key lookup. The test does assert the fix.
- Test for f2: the counts test now submits a holding check and gives an open down-vote. It asserts `checks == checks list counts`, that `holds` and `no check` are both present, and that `feedback == 1`.
- Test for f3: the never-fails test asserts `{"namespaces": []}` for an empty repo, and an empty `namespaces` list plus a non-empty `unavailable` for a broken store. The CLI help, the epilog, docs/commands.md and the module docstring all describe this. The overview row's "opens each store read-only" is still true.

## Findings

- f1: resolved in briefing.py:61-79 (read-only open, backup into memory, migrate the copy) and covered by test_briefing.py:91.
- f2: resolved in test_briefing.py:64-84.
- f3: resolved in cli.py (the JSON error object and the help text) and docs/commands.md (the empty-list and `unavailable` sentences).

## Notes

`_read_only` builds a `Store` without calling its constructor. That is fine today because `_migrate` and the readers use only `path` and `db`. If `Store` gains state that its methods read, this will break, and the tests here would catch it.
