---
type: verdict
title: 'Verdict: plugin-remove reviewer round 2'
description: 'reviewer verdict for round 2 of plugin-remove: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T08:32:03+00:00'
slug: plugin-remove
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All four findings from round 1 are fixed, and the fixes break nothing they touch. The stamp is green. The change can be committed.

## Checked

- Gates: I re-ran `loopctl gate stamp` from the worktree with a fresh empty scratch HOME. Result: `stamp green: ed722537e68a95ebfb2c7872a26d27fcd1407797b633f37b2f75dc6c500c0979`. Lint, format, tests, integration and eval rows r1 to r8 all pass. The fingerprint matches the round's binding. The state commit was skipped because the scratch HOME has no git identity. The tree is unchanged.
- f1: `_report_remove` now has three cases. With nothing removed and `kept` non-empty, it prints "removed nothing; kmctl is installed for X (scope)". `remove` returns `installed` as `kept` when nothing was removed, so the line is right. test_remove_summary_names_the_harness_still_installed asserts that exact text, and the old code would fail it.
- f2: `_require`, `_apm` and `_apm_run` take `again` and default to `kmctl plugin install`, so install's messages do not change. `remove` passes `REMOVE_AGAIN` to the uninstall and to `claude mcp remove`. The uvx-missing message in `_apm_run` uses it too. The reinstall inside remove keeps the install wording, and the remove wrapper adds the full `kmctl plugin install --harness ... --source ...` command, so that message is still correct. test_remove_failure_names_remove_not_install makes the uninstall fail and asserts stderr ends with "then kmctl plugin remove again".
- f3: the commands.md table row now lists `install`, `update`, `remove`, which matches the typer group's help.
- f4: the r3 test sets a mirror `git:` URL with ref v0.0.9. It asserts that the uninstall name comes from the mirror and that the reinstalled entry keeps both the mirror and the ref.

## Findings

- f1: resolved in src/kmctl/__init__.py `_report_remove`.
- f2: resolved in src/kmctl/plugin.py `_require`/`_apm`/`_apm_run`, with `REMOVE_AGAIN` passed by `remove` and `_remove_mcp`.
- f3: resolved in docs/reference/commands.md, the `kmctl plugin` row.
- f4: resolved in tests/test_plugin_remove.py around line 243.

## Notes

`read_manifest` and `read_json` still end their malformed-file errors with "fix it, then run kmctl plugin install again", and remove can reach both, for example through a broken settings.json. After fixing the file, rerunning install does no harm, but the hint is a little off for remove. This is outside f2 as written, and I am not asking for a change.
