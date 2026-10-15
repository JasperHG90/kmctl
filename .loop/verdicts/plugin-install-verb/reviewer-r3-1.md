---
type: verdict
title: 'Verdict: plugin-install-verb reviewer round 3'
description: 'reviewer verdict for round 3 of plugin-install-verb: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:32:45+00:00'
slug: plugin-install-verb
pass: reviewer
round: 3
body_schema: verdict/1
---

## Summary

f6 is fixed, and the fix broke nothing it touched. Both version-mismatch problems in status now name `kmctl plugin update`. The only install hints left are for "not installed here" and a missing marketplace folder, and install works in both cases. Pass.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1 to r6 pass, "stamp green: bfcdef7dde761b033b03a985e4a8b554fa78c92123195dd60cbeab4c7deb16fa". That matches the round's fingerprint. All 9 tests in tests/test_plugin_install.py ran, none skipped, so claude is on PATH.
- Read status(), install() and _entry() in src/kmctl/plugin.py, and the new test.
- The new test patches cli_version after an install. The installed copy and the staged copy then both mismatch, so the assertion that "kmctl plugin install" is not in the status output directly covers f6. The test also covers f7: the plain install exits 1 naming update, and update leaves no problems.
- r5 still asserts "mismatch" for a staged-copy change and the install hint for a missing path, both of which still hold. update tolerates a missing install, because its uninstall step ignores failure, so the update hint is never a dead end.

## Findings

- f1, f2, f3, f4, f5: resolved in round 2, unchanged.
- f6: resolved at plugin.py:205.
- f7: resolved by tests/test_plugin_install.py::test_installed_version_check_after_upgrade.
