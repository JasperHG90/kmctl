---
type: spike
title: Spike antigravity-harness/1
description: does uv run <raw GitHub URL of okf_mcp.py> start the okf MCP server, answer initialize over stdio and list its three tools, with and without a bundle-dir argument?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T19:48:32+00:00'
slug: antigravity-harness
n: 1
outcome_written: true
---

# Spike antigravity-harness/1

does uv run <raw GitHub URL of okf_mcp.py> start the okf MCP server, answer initialize over stdio and list its three tools, with and without a bundle-dir argument?

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-r2/mcp_probe.py
```

## Outcome

`uv run <raw URL>` (uv 0.13.0, pinned commit a8b9642) started okf's MCP server over stdio in all three cases: `initialize` returned serverInfo `{"name":"okf","version":""}` and protocol 2025-06-18 in 0.5-1.1 s, and `tools/list` gave get_neighbors, read_concept, search_concepts.
`search_concepts("hello")` found the test concept when cwd held `.okf/` (no arg) and when cwd was elsewhere with the bundle dir passed as the first argument (`uv run <url> <proj>/.okf`).
With cwd elsewhere and no argument the server still started, but every tool call failed with "no OKF bundle at .okf", so the cwd matters: pass the bundle path (the `.okf` folder itself) or set `$OKF_BUNDLE` when the host's cwd is not the project root.
Rules out the need to ship a local copy; settles risk 2. Limits: uv's package cache was warm (29 packages installed in 45 ms), so a cold first start was not timed; serverInfo version is empty when run from a URL because the script reads it from a sibling plugin.json.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/mcp_probe.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-ag-r2/mcp_probe.py`, which the command used
