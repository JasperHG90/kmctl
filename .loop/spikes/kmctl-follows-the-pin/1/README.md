---
type: spike
title: Spike kmctl-follows-the-pin/1
description: does a tag-pinned uvx or uv tool install of kmctl warm the uv cache a commit-pinned uvx --from git+...@SHA uses, and how long does the cold commit-pinned run take?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:47:52+00:00'
slug: kmctl-follows-the-pin
n: 1
outcome_written: true
---

# Spike kmctl-follows-the-pin/1

does a tag-pinned uvx or uv tool install of kmctl warm the uv cache a commit-pinned uvx --from git+...@SHA uses, and how long does the cold commit-pinned run take?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin1/warm.sh
```

## Outcome

Exit 1 comes only from the 500 ms bar in (d): the commit-pinned uvx took 661 ms after `uv tool install git+...@v0.6.0`, against 8787 ms cold. Every other bar passed. With an empty cache (uv 0.13.0), cold `uvx --from git+...@<sha> kmctl --version` took 8787 ms; run again 132 ms, and `--offline` 134 ms.
A tag-pinned `uvx` warms the commit form: 3045 ms for the tag, then 385 ms for the sha and 110 ms with `--offline`. A tag `uv tool install` (2849 ms) also warms it: 661 ms, then 135 ms with `--offline`. The offline runs passing shows nothing was rebuilt.
This rules out the half of risk 1 that says a tag-pinned run or install leaves the sha-pinned cache cold. The warm-up in `just kmctl` helps.
Limit: the clone came from a local file:// bare repo (56 MB), so GitHub will be slower. The 8.8 s cold time is a lower bound, and this run did not measure it against a hook's timeout over the network.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/warm.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin1/warm.sh`, which the command used
