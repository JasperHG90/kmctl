---
type: spike
title: Spike opencode-harness/6
description: with apm-cli 0.33.0 and targets [opencode], does a first apm install with no .opencode/ write okf-bundle into opencode.json as a valid OpenCode local server that answers MCP initialize, and keep pre-seeded instructions and theme keys on reinstall?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-17T21:54:45+00:00'
slug: opencode-harness
n: 6
outcome_written: true
---

# Spike opencode-harness/6

with apm-cli 0.33.0 and targets [opencode], does a first apm install with no .opencode/ write okf-bundle into opencode.json as a valid OpenCode local server that answers MCP initialize, and keep pre-seeded instructions and theme keys on reinstall?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/4/opencode-mcp.sh
```

## Outcome

Exit 0: all four parts hold with apm-cli 0.33.0 and `targets: [opencode]`, for a local package holding kmctl's skills, its auditor agent and the okf-bundle entry copied from apm/apm.yml. (a) A first install with no `.opencode/` wrote okf-bundle to opencode.json, because the agents step created `.opencode/agents/` before the MCP step ran; a second plain install left opencode.json byte for byte unchanged. (b) The entry is `{"type": "local", "enabled": true, "command": ["sh", "-c", LAUNCHER]}`, with the command equal to `[sh] + args` from apm.yml and no keys outside OpenCode's McpLocalConfig (packages/core/src/v1/config/mcp.ts, sst/opencode 9d97a5b). (c) After `instructions: [".opencode/rules/*.md"]` and `theme: "x"` were added, a reinstall kept both keys and the entry (APM reads opencode.json, merges into `mcp`, and writes the result back). (d) Running the entry's command in a repo with `.okf/` answered an MCP initialize in 0.4 s with serverInfo name "okf" (warm uv cache).
Settles risk 4. Limit: `.opencode/` exists at MCP time only because APM deploys an agent there. If the plan stops deploying APM's agent to `.opencode/agents/`, a first install would skip the server (the adapter returns early with no `.opencode/`). APM also warned that kmctl-auditor's `tools` is a string, which OpenCode rejects; that matters for risk 2.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/opencode-mcp.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/4/opencode-mcp.sh`, which the command used
