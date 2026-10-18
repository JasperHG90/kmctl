---
type: spike
title: Spike kmctl-follows-the-pin/4
description: with an empty uv cache, does uvx --offline --from git+...@SHA fail fast and nonzero without the network, or does it still git-fetch the source?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:51:18+00:00'
slug: kmctl-follows-the-pin
n: 4
outcome_written: true
---

# Spike kmctl-follows-the-pin/4

with an empty uv cache, does uvx --offline --from git+...@SHA fail fast and nonzero without the network, or does it still git-fetch the source?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin3/miss.sh
```

## Outcome

With a fresh empty cache per case (uv 0.13.0), `uvx --offline --from git+https://github.com/JasperHG90/kmctl@<sha> kmctl --version` against the real GitHub URL failed in 61 ms with rc 1 and no IPv4/IPv6 connects (strace); `UV_OFFLINE=1` took 66 ms, an unroutable host 80 ms, a missing source path 97 ms. uv refuses remote git fetches offline: "Remote Git fetches are not allowed because network connectivity is disabled (i.e., with `--offline`)".
This rules out a hang, a network attempt or a slow failure on a cache miss, well inside the hooks' 10 s. A cache warm with another commit (v0.5.1) also misses fast (55 ms, rc 1).
uv still runs `git fetch` for file:// remotes when offline: with the source reachable on disk it built the commit offline in 4.5 s (and 5.3 s in spike 3). That only matters when insteadOf points at a local path, never for the GitHub URL.
A miss exits 1, the same code the child can return (spike 3: uvx passes child codes 1, 2 and 7 through unchanged, with no stderr of its own). The exit code alone cannot tell them apart. stderr can: a miss starts `error: Failed to resolve` and mentions `--offline`/"network was disabled"; a warm kmctl run prints neither.
Settles risk 1 if kmctl tells a miss from a failure by uv's stderr (or by a warm `--version` probe first), not by exit code. Limit: Linux, uv 0.13.0.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/miss.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin3/miss.sh`, which the command used
