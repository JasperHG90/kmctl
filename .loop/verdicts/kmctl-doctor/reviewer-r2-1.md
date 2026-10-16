---
type: verdict
title: 'Verdict: kmctl-doctor reviewer round 2'
description: 'reviewer verdict for round 2 of kmctl-doctor: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T22:15:52+00:00'
slug: kmctl-doctor
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both findings sent back are settled. The claude.old-plugin fix now depends on which plugin is enabled: the install fix when kmctl@kmctl is enabled, otherwise `claude plugin uninstall okf@scaccogatto` at the scope of the file that enables it. f2 was wrong: the repo rule `.claude/rules/httpx-for-http.md` requires httpx over urllib.request. The gates pass.

## Checked

- Ran `loopctl gate stamp` in the worktree with HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME set to scratch folders. Lint, format, tests and integration pass, and so do rows r1 through r8. Result: `stamp green: c783b53f01b78f29065f9cb3d91fb8334023efdad67088a76525fe6118ba34c1`, the same fingerprint this round is bound to.
- Read `_old_plugins`, `_kmctl_mark`, `harnesses_found` and `_claude_old_plugin` in src/kmctl/doctor.py. The scope mapping is right: `--scope user` for the user settings file, `--scope local` for settings.local.json, otherwise `--scope project`. When kmctl@kmctl and okf are both enabled, the install fix comes first. If okf was not kmctl's dependency it stays enabled, and the next doctor run names its uninstall. So the advice always reaches ok within a few runs, and no fix line points at a command that does nothing.
- `_kmctl_mark` now counts only kmctl@kmctl. An okf plugin the user chose on their own no longer marks the claude harness as installed, so doctor does not report a kmctl problem in a repository without kmctl. This fits the plan, which treats the old plugin as a trace of a kmctl install.
- Tests: the parametrized `test_old_plugin_enabled_fails_with_its_fix` checks the full ending of the fix for every case: kmctl alone in both files, both plugins, and okf alone at project and local scope. It also checks that only uv was called, never claude. `test_old_plugin_at_user_scope_names_the_scope` covers `--scope user`. `test_old_okf_plugin_alone_does_not_mark_the_claude_harness` would fail if okf marked the harness again, because then the old-plugin check would run and fail.
- docs/reference/commands.md: the claude.old-plugin row describes both fixes and matches the code.
- f2: read `.claude/rules/httpx-for-http.md`. It applies to `**/*.py` and requires httpx with one client used as a context manager and an explicit timeout. doctor.py:521 does exactly that.

## Findings

- f1 resolved: src/kmctl/doctor.py:420-447 picks the fix by plugin and scope, and tests/test_doctor.py:842-914 assert each fix line.
- f2 withdrawn: the repository's httpx-for-http rule requires httpx for HTTP calls, so keeping httpx and respx is correct.

## Notes

The plan text says the fix for claude.old-plugin is `kmctl plugin install --harness claude` in every case. The change departs from that only for okf on its own, because of f1, and the reference doc records it. With scratch HOME, the stamp's own git commit failed for lack of a git identity, which left the stamp file staged in the primary checkout.
