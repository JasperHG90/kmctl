---
type: spike
title: Spike plugin-patch/1
description: 'over a stale okf-bundle (older pin): apm install skips it; after deleting okf-bundle from .mcp.json and .agents/mcp_config.json, does a second plain apm install write the package''s server back to both?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:55:46+00:00'
slug: plugin-patch
n: 1
outcome_written: false
---

# Spike plugin-patch/1

over a stale okf-bundle (older pin): apm install skips it; after deleting okf-bundle from .mcp.json and .agents/mcp_config.json, does a second plain apm install write the package's server back to both?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-mcp-again.sh
```

## Outcome

Not written yet: `loopctl plan spike-note plugin-patch 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-mcp-again.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-mcp-again.sh`, which the command used
