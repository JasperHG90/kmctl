---
type: verdict
title: 'Verdict: plugin-install-verb reviewer round 1'
description: 'reviewer verdict for round 1 of plugin-install-verb: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:18:29+00:00'
slug: plugin-install-verb
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The happy path works against a real claude 2.1.300: install pulls okf at project scope, a rerun is stable, update after a bump lists the new version, and the wheel carries the plugin. But the version check the plan requires is dead code (f1), and status and the okf-marketplace check ignore scope and project (f2, f3), which a manual run with an isolated config showed. Fail.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1 to r6 all pass, "stamp green: 056cb4a331e3bcaef9bcbd934aebe77551419b107a7898dcf258559e00a3dd59". With `-rs` the claude tests ran (6 passed), not skipped.
- Read the staged diff: pyproject.toml, src/kmctl/__init__.py, src/kmctl/plugin.py, tests/test_plugin_install.py, against the plan, spikes 1 and 3, and the cli-interface, cli-version-floor and type-hint rules.
- Manual runs with CLAUDE_CONFIG_DIR and XDG_DATA_HOME in the scratchpad: install, install with cli_version patched to 0.2.0 (f1), status and update, then status and install from a second git repo (f2, f3).
- Rows: r3 to r6 tests assert their fails_when. r1 and r2 are weaker than their rows (f4). No row covers install after an upgrade without update, which is where f1 hides.
- mypy on src/kmctl (f5). Help for the plugin group and verbs renders at 80 columns and is covered by test_help.

## Findings

- f1: in claude's list, `version` is the installed cache version and `folderVersion` is read live from the staged folder. stage() has just written cli_version there, so `installed == cli_version()` always holds after install, and the plan's "list must show this version, else say run kmctl plugin update" can never fire. Reproduced: plain install at 0.2.0 over 0.1.0 exited 0, and claude still listed 0.1.0. Compare against `version`. Blocking, because the fix changes what status reports and what the r5 test relies on.
- f2: the presence check reads `marketplace list`, which merges every scope. Reproduced in a second repo: its .claude/settings.json declared only the kmctl marketplace but enabled okf@scaccogatto. Blocking, because the fix changes the install order that the r2 idempotency test covers.
- f3: reproduced in a second repo before installing: `status --json` gave plugin_version 0.2.0 and a mismatch problem taken from the first repo's entry. Filter by scope and, for project scope, by projectPath == cwd. Status may need --scope for this. Blocking, because it is the same lookup f1's fix uses.
- f4: non-blocking, since the code passes these checks today and the fix only tightens assertions. Assert `scope == "project"` for both ids, compare the whole list (or the entries without timestamps), and assert the first result's exit code.
- f5: non-blocking, since it is a one-word annotation fix. Per the pre-existing-issues rule, the two older mypy errors should be fixed too.

## Notes

The `marketplace add` fallback runs `marketplace update` on any failure, not only "already registered". That matches loopctl and is acceptable for now.
