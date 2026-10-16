---
type: verdict
title: 'Verdict: antigravity-harness reviewer round 1'
description: 'reviewer verdict for round 1 of antigravity-harness: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T21:38:49+00:00'
slug: antigravity-harness
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. `kmctl plugin install --harness antigravity` runs APM with `--target antigravity` and rewrites `.agents/plugins/kmctl/` with plugin.json, a named SessionStart hook, three translated agents and okf's MCP server. `kmctl briefing --format antigravity` reads `workspacePaths[0]` from stdin, and status compares the folder file by file. The gates and all nine eval rows are green on my own stamp, and agy really validated the folder (r6 ran, it was not skipped). Two small non-blocking findings: one status fix line points Antigravity users at the wrong command, and one docstring names a command that does not exist yet.

## Checked

- Ran `loopctl gate stamp` from the worktree with scratch HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME. Every gate passed (lint, format, tests, integration) and rows r1 to r9 passed: "stamp green: 02cb8dd9e7573221448ed24155b7138182f846a669dde340ddbec79e53572a20". The state commit was deferred only because the scratch HOME has no git identity. The r6 log shows "1 passed" with agy at /home/vscode/.local/bin/agy, and r7 ran the real APM 0.33.0 against the served tree.
- Read in full: src/kmctl/antigravity.py, tests/test_antigravity.py, and the diffs to briefing.py, plugin.py, __init__.py, conftest.py, test_apm_package.py, test_check_wheel.py, pyproject.toml, check_wheel.py, ADR 0015, ADR 0003, the manifesto, the overview, the commands reference, the install how-to and the README.
- Eval rows against their tests:
  - r1: each tool mapping, the Bash and no-Bash policy cases, the dropped keys (list(meta) is exact), an unchanged body (three sources) and the named refusal of an unknown tool are all asserted.
  - r2: the exact file set, the hooks.json value, the translations, and the MCP sha read from apm/apm.yml are asserted. The launcher runs for real with a fake uv from the plugin folder (PLUGIN_ROOT unset), from a subfolder and from elsewhere with PLUGIN_ROOT set. Two installs are compared byte for byte.
  - r3: the JSON shape is checked exactly. TEXT is compared with `kmctl briefing --path`. Stdin is read from another folder, both in-process and as a real subprocess. The fallbacks for empty input, non-JSON, a list, empty paths, a missing folder and a terminal are covered, and the default and `--json` stay the same.
  - r4: the real HOOK_COMMAND runs under /bin/sh with no kmctl, and with a kmctl that fails after printing partial output. Both cases assert exit 0 and `{}`.
  - r5: an edited, a deleted and an added file are each reported with the fix.
  - r8: the docs tests check the decision schema and sections and the required phrases.
- Judged the builder's choices, and all are sound:
  - `--scope user` with antigravity is refused in preflight before anything runs, and status reports it.
  - The auditor comes from the wheel's kmctl/_agents, and the wheel check and test were extended for it. okf's agents come from apm_modules/.
  - The server is named `bundle` with no "type" (agy validate accepts it).
  - The launcher's start `${PLUGIN_ROOT:+$PLUGIN_ROOT/../../..}` resolves to the repository root for `.agents/plugins/kmctl`.
  - `--format antigravity --json` raises BadParameter and exits 2, as documented.
  - The fixtures moved to conftest.py unchanged.
  - The README now describes the APM package for both harnesses.
- Reproduced f1 in a scratch repository with an old resolved_ref.

## Findings

- f1: in `status`, the version-mismatch line still ends with `run kmctl plugin update{suffix}` with no harness, while the other problems now name `--harness ...`. I reproduced it: `kmctl plugin status --harness antigravity` printed "...; run kmctl plugin update". `plugin update` defaults to `--harness claude`, so it does the wrong install for an Antigravity repository. The install how-to already tells Antigravity users to run `kmctl plugin update --harness antigravity`, so the status line contradicts it. Fix: append `--harness <harnesses>` when they are not just claude, and add a test. Non-blocking because the fix is one string.
- f2: src/kmctl/antigravity.py lines 10-11 say "so `kmctl plugin status` and `kmctl doctor` share one comparison". kmctl has no doctor command. Say only plugin status uses it, or say doctor will.

## Notes

The two known gaps the briefing names are left to antigravity-live-check: a stdin that Antigravity leaves open could stall the hook until its 10 s timeout, and the briefing text says `.claude/rules/` on both harnesses. I did not raise them here.
