---
type: spike
title: Spike antigravity-harness/3
description: does agy discover a plugin placed in a workspace .agents/plugins/NAME/ folder (offline check via agy agents)?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T19:50:35+00:00'
slug: antigravity-harness
n: 3
outcome_written: true
---

# Spike antigravity-harness/3

does agy discover a plugin placed in a workspace .agents/plugins/NAME/ folder (offline check via agy agents)?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-r1/probe.sh
```

## Outcome

agy 1.4.0, offline, scratch HOME, no user-level plugins: `agy agents` listed `kmctl-probe`, the agent inside a workspace `.agents/plugins/kmctl/` (plugin.json, named-hook hooks.json, agents/x.md). It did this from the repo root and from `repo/sub`, walking up to `.agents/`. So Antigravity's own customization loader discovers a workspace plugin folder, and a user-level plugin under `~/.gemini/` is not needed. `validate --strict` reported agents 1, hooks 1, no findings.
Gate: discovery only happens in a trusted workspace. Untrusted, nothing was listed. Trust (`trustedWorkspaces` in `~/.gemini/antigravity-cli/settings.json`, which the trust dialog writes) matches the exact working folder. With only the root trusted, running from `repo/sub` listed nothing. The plan and docs should tell users to trust the folder.
`agy plugin list --json` printed `[]` throughout: it lists installed plugins only, so it is no evidence either way.
Partly settles risk 1: plugin discovery and agent loading are shown. A live session is still needed to see the SessionStart hook fire and the MCP server start, because offline `agy` has no way to list hooks or MCP servers.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/probe.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-r1/probe.sh`, which the command used
