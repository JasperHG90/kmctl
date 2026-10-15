---
type: verdict
title: 'Verdict: plugin-install-verb reviewer round 2'
description: 'reviewer verdict for round 2 of plugin-install-verb: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:25:47+00:00'
slug: plugin-install-verb
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All five findings sent back are fixed, and I reproduced each fix against claude 2.1.300 with an isolated config. Two small gaps remain, neither blocking: status gives two different fix commands after an upgrade (f6), and no test covers the installed-version check that f1 added (f7). Fix.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1 to r6 all pass, "stamp green: 59c7d2b3165d159139d3a7e2a721ff6f6496adff8ce0d41a3f66af9e49d44193", which matches the round's fingerprint. claude is on PATH, so the claude tests ran rather than skipped.
- Read plugin.py in full, the plugin and review_due.py hunks of the diff, and tests/test_plugin_install.py.
- Manual runs with CLAUDE_CONFIG_DIR and XDG_DATA_HOME in the scratchpad and cli_version patched: install at 0.1.0 (exit 0), plain install at 0.2.0 (exit 1, "claude lists kmctl@kmctl at 0.1.0, not 0.2.0; run kmctl plugin update"), status (installed 0.1.0 mismatch), update (0.2.0, no problems). In a second repo: status says "not installed here", install exits 0 and its .claude/settings.json declares both scaccogatto and kmctl marketplaces. A user-scope install from a third repo is seen by status there, and the first repo's project entry still wins over the user entry.
- mypy on src/kmctl: only the missing yaml stubs remain.
- Rows r1 to r6: each test asserts its fails_when.

## Findings

- f1: resolved at plugin.py:186; the post-install check now fires, as reproduced above.
- f2: resolved at plugin.py:158; the second repo's settings declare scaccogatto.
- f3: resolved in `_entry`; test_status_ignores_other_repositories covers it and my run agreed.
- f4: resolved; the r1 and r2 tests now check scope, projectPath and the first exit code.
- f5: resolved; mypy is clean apart from third-party stubs.
- f6: non-blocking, because a plain fix (change the hint text, or drop the staged problem when the installed one is reported) cannot ship a defect. Every path still ends at update.
- f7: non-blocking, because the behaviour works, as I checked by hand, and the fix only adds a test (patch cli_version after an install, then assert install exits 1 and status reports "installed plugin").
