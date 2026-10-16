---
type: spike
title: Spike antigravity-harness/4
description: does a workspace .agents/plugins/NAME/ plugin's SessionStart hook fire and its MCP server start under agy, with which cwd and PLUGIN_ROOT?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:23:12+00:00'
slug: antigravity-harness
n: 4
outcome_written: true
---

# Spike antigravity-harness/4

does a workspace .agents/plugins/NAME/ plugin's SessionStart hook fire and its MCP server start under agy, with which cwd and PLUGIN_ROOT?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-probe/probe.sh
```

## Outcome

agy 1.4.0 found the workspace plugin's hook: `-p hi` logged "loaded 1 named hooks from 1 hooks.json file(s)", and `plugin validate` counted 1 hook and 1 MCP server.
Neither the SessionStart hook nor the MCP server ran: hook.log and mcp.log never appeared. Without auth, `-p` stopped at "authentication required". With a copy of the real auth token it stopped at "Eligibility check failed". The agy log has no MCP lines at all.
`agents`, `mcp list` and `plugin list` do not start a session, and `mcp list` does not show plugin MCP servers ("No MCP servers configured").
So the hook and MCP server start after the eligibility check, if they start at all. The cwd, PLUGIN_ROOT and `$PLUGIN_ROOT` expansion are still unknown.
Does not settle risk 1. This still needs a live session on an eligible account.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/probe.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-probe/probe.sh`, which the command used
