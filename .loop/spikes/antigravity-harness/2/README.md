---
type: spike
title: Spike antigravity-harness/2
description: does agy discover a plugin placed in a workspace .agents/plugins/NAME/ folder (offline check via agy agents)?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T19:50:08+00:00'
slug: antigravity-harness
n: 2
outcome_written: true
---

# Spike antigravity-harness/2

does agy discover a plugin placed in a workspace .agents/plugins/NAME/ folder (offline check via agy agents)?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-r1/probe.sh
```

## Outcome

Not the deciding run; spike 3 replaces it. With the repo root in `trustedWorkspaces`, `agy agents` (agy 1.4.0, offline) listed `kmctl-probe`, the agent inside `.agents/plugins/kmctl/`. With no trust it listed nothing. From `repo/sub` it also listed nothing, which made the run exit 1.
A manual follow-up showed the subfolder miss comes from trust, not discovery: trust matches the exact working folder. Once `repo/sub` was trusted, the agent was listed from there too.
`agy plugin list --json` printed `[]` in every case, so it shows only user-level installed plugins and cannot answer this question.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/probe.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-r1/probe.sh`, which the command used
