---
type: spike
title: Spike apm-hands-back/2
description: in agy 1.4.0, does a SessionStart hook in the workspace .agents/hooks.json (named apm, as APM writes it) inject the kmctl briefing, and does okf's server in .agents/mcp_config.json answer search_concepts?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:47:55+00:00'
slug: apm-hands-back
n: 2
outcome_written: true
---

# Spike apm-hands-back/2

in agy 1.4.0, does a SessionStart hook in the workspace .agents/hooks.json (named apm, as APM writes it) inject the kmctl briefing, and does okf's server in .agents/mcp_config.json answer search_concepts?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-agy-ws.sh
```

## Outcome

Exit 0: APM's workspace files work in agy 1.4.0. In a trusted scratch repository after kmctl init, with only .agents/hooks.json = {"apm": {"SessionStart": [kmctl's guarded briefing command]}} and .agents/mcp_config.json declaring okf-bundle with kmctl's sh launcher (the shapes APM 0.33.0 writes) and no plugin folder, an agy -p session on gemini-3.8-flash-high quoted the briefing's first line, kmctl briefing (kmctl 0.3.0), and call_mcp_tool okf-bundle/search_concepts returned decisions/0001-keep-project-knowledge-in-an-okf-bundle. So the hook name apm, the workspace hooks.json and the workspace mcp_config.json all load, and the launcher finds .okf/ from the server's working folder.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-agy-ws.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-agy-ws.sh`, which the command used
