---
type: spike
title: Spike opencode-harness/5
description: with apm-cli 0.33.0 and targets [opencode], does a first apm install with no .opencode/ write okf-bundle into opencode.json as a valid OpenCode local server that answers MCP initialize, and keep pre-seeded instructions and theme keys on reinstall?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-17T21:54:47+00:00'
slug: opencode-harness
n: 5
outcome_written: true
---

# Spike opencode-harness/5

with apm-cli 0.33.0 and targets [opencode], does a first apm install with no .opencode/ write okf-bundle into opencode.json as a valid OpenCode local server that answers MCP initialize, and keep pre-seeded instructions and theme keys on reinstall?

The command timed out:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/4/opencode-mcp.sh
```

## Outcome

Timed out at 300 s, which says nothing about the risk. Parts (a) to (c) printed the same results as spike 6. The check script then hung reading the server's stderr after kill, because uv's child process kept the pipe open. The script was fixed and rerun as spike 6, which is the one to cite.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/opencode-mcp.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/4/opencode-mcp.sh`, which the command used
