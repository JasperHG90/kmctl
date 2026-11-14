---
type: verdict
title: 'Verdict: kmaudit-briefing reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-briefing: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T14:19:04+00:00'
slug: kmaudit-briefing
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The briefing is correct and read-only on current stores, and it matched the list commands on a copy of the operator's old store. It fails on older stores, though. Any store before schema step 5 makes the whole briefing print "unavailable" when the plan says to count missing tables as empty. Because of that one blocking bug the verdict is fail. The other two findings are a weak test and a docs gap.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r4 all pass, "stamp green: 2c10de2def90e4979788477c66e10928959191f867489bf9aa9fb9ea30284a5c".
- Read briefing.py, the cli.py verb, test_briefing.py, the README and commands.md changes, and the .okf architecture and log edits. I also read the code they call: `Store.__init__` (to confirm the briefing skips every write it does), `status_row`, `check`, `feedback.latest` and `is_open`, `previous_keys`, and `namespaces.existing` and `listing`.
- Real data: I copied the operator's .kmctl/audit.sqlite (just the file; there was no -wal) into a scratch git repo that holds this tree's .okf. `kmaudit briefing` printed 207 sections (25 pending), 1281 claims, 1 open note, and checks of 708 holds, 80 not measured, 117 reason, 229 stale reason and 1 weak. It ran in 0.2s. Afterwards the sha256 still matched, no .kmaudit/ appeared, and only -wal and -shm sidecars were added. Then `checks list --json` gave the same status counts, and `claims list --json` gave 207 sections and 1281 claims.
- Old schema steps: I rebuilt the fixture store at steps 1, 2, 4 and 5 (script at /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/old_step.py). Steps 1, 2 and 4 raise OperationalError ("no such table: checks" or "no such table: feedback"), so the CLI prints "unavailable". Only step 5 briefs.
- Rows: r2's test moves the store to the legacy path, edits a page, then checks that every .sqlite hash is unchanged, that no .kmaudit/ exists and that pending went up by exactly one. That asserts its fails_when. r3's test makes stale == every section, carried == every - extracted, and checks that `todo` agrees, so it really tests PREVIOUS_HASHES. r4's test covers both an empty repo (no output, exit 0) and a garbage store (one line, exit 0). r1: see f2.
- Docs: the overview row, the audit-pipeline verb list and the README hook snippet agree with the code. Apart from f3, the docstrings are accurate.

## Findings

- f1: `brief_one` guards the sections count and its own `latest(store)` call against OperationalError, but `status_row` calls `check(store, ...)` (the checks table, added in step 2) and `latest(store, [id])` (the feedback table, added in step 5) unguarded. A kmctl-era store from before the feedback table, which is exactly the legacy store this verb promises to read, gets no briefing at all. The hook still exits 0, so no session is blocked, but the plan's contract ("reads whatever schema step the file is at ... counts a missing table as empty") is broken, and no test covers an older step. It is blocking because the fix touches how statuses are counted. A careless fix, such as catching OperationalError around the whole status loop, would silently report every claim as having no status. Add a test at an early step.
- f2: Add a stored check (or reason) and one open plus one answered feedback row to the r1 fixture, so that `checks` and `feedback` are compared in a case where they can differ.
- f3: Either print nothing with --json when there is no namespace, or say in the docs and help that --json prints an empty list. Also say that the unavailable line is plain text even with --json, or emit a JSON error object there.

## Notes

`store.claims()` is called twice in `brief_one`, once for the checkable set and once for the count. That is harmless.
