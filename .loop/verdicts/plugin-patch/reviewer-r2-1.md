---
type: verdict
title: 'Verdict: plugin-patch reviewer round 2'
description: 'reviewer verdict for round 2 of plugin-patch: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T15:56:59+00:00'
slug: plugin-patch
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All four round-1 findings are fixed, and the fixes break nothing they touch. A fresh stamp is green on every gate and every eval row, and it binds the same fingerprint as this round. The change can be committed.

## Checked

- Gates: I ran `loopctl gate stamp` in the worktree with a fresh, empty scratch HOME. Result: pass for lint, format, tests and integration, and for eval rows r1 to r7. `stamp green: 685533460b0a0d7dc18477cc18f743b77784e9f896463a146a4ae7ce0246a844`, which matches the round-2 binding. The state commit was deferred only because the scratch HOME has no git identity.
- f1: read in full `read_json` and the YAML reader next to it. Every branch now ends in "fix it, then run the command again". test_patch_refuses_settings_that_are_not_json checks exit 1, the message, that "plugin install" is absent, and that the file is left alone.
- f2: read the restored tests at tests/test_plugin_patch.py:440-626. They cover remove_old_plugin through patch: another repository's plugin left alone, user scope, a marketplace that is already gone, an uninstall failure that names its cause and "kmctl plugin patch again", and claude missing from PATH. They cover drop_old_hook with a shared group and with nothing recorded, drop_old_mcp keeping a current server at user scope, and uninstall_name for https, a host with a port, scp-style URLs and the string form. Each test asserts real behaviour, not a constant.
- f3: `_apm_run` is gone from src/. The HARNESSES and DEFAULT_SOURCE comments now describe what the constants are for. `unpatch` now returns the scope it is given, and test_undo_reports_the_scope_given asserts `scope: user`. The text Next line for `--undo --scope user` names `kmctl doctor --scope user`, which is correct.
- f4: the rule's title is now "The package matches the CLI", and its constraint is `the-package-is-installed-at-the-cli-tag`. Both match the body: the apm.yml entry at the CLI tag, apm install, then plugin patch. The test_apm_package.py and test_antigravity.py docstrings now describe APM 0.33.0 plus kmctl plugin patch.

## Findings

- f1: resolved at src/kmctl/plugin.py:425.
- f2: resolved in tests/test_plugin_patch.py:440-626.
- f3: resolved in src/kmctl/plugin.py (comments at lines 31-36, `_apm_run` removed, `unpatch` scope).
- f4: resolved in .claude/rules/cli-version-floor.md and the two test docstrings.

## Notes

- These comments were outside the findings sent back, so they do not block. Fix them in passing:
  - tests/test_network_retry.py:17 still says the plugin tests "run the real kmctl plugin install"; they now run apm install and kmctl plugin patch.
  - tests/test_init.py:170 says rules come from kmctl plugin install.
  - The section comment in tests/test_plugin_patch.py:440 names "Review round 1 f2". That is loop history, not a description of the tests.
