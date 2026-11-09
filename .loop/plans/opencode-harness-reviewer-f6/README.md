---
type: plan
title: 'Plan: opencode-harness-reviewer-f6'
description: Deferred hardening from opencode-harness, reviewer finding f6 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T04:59:58+00:00'
slug: opencode-harness-reviewer-f6
epic: multi-harness
depends_on: []
priority: null
---

# opencode-harness-reviewer-f6

Relayed from: opencode-harness, reviewer finding f6 in review round 1

## Intent

`kmctl plugin patch --undo` ignores `--scope`. `unpatch` in
`src/kmctl/plugin.py` deletes the Antigravity plugin folder and runs
`kmctl.opencode.undo` in the working folder whatever the scope. So
`kmctl plugin patch --undo --scope user`, run from a repository to undo a
user-scope Claude Code install, also deletes that repository's
`.agents/plugins/kmctl/` and its OpenCode agents, rules, plugin and
`instructions` entry. The help says Antigravity and OpenCode are patched at
project scope only, and `patch --scope user` already leaves OpenCode alone
and says so.

What changes: at `--scope user`, `unpatch` deletes nothing in the working
folder. When it finds kmctl's project-scope files there (the Antigravity
plugin folder or any OpenCode file `kmctl.opencode.undo` would remove), it
prints one note naming them and saying to run `kmctl plugin patch --undo` in
the repository without `--scope user`. At project scope nothing changes.
`docs/reference/commands.md` and the `--undo` help say so. Tests in
`tests/test_plugin_patch.py` and `tests/test_opencode.py`.

Measured on 2026-10-18 in a scratch repository with a patched OpenCode
install and an Antigravity plugin folder: `kmctl plugin patch --undo --scope
user` deletes 12 files there today (the plugin folder's 4, OpenCode's 3
agents, 4 rules and plugin) and rewrites `opencode.json` (a script run from
the session scratchpad over `tests/test_opencode.py`'s fake install); the
outcome is 0 deleted, 0 changed, and one note naming them.

Done when: `--undo --scope user` in such a repository leaves every file
byte for byte as it was and prints the note; `--undo` at project scope
behaves as before; and the gates pass.

## Could invalidate this plan

- none
