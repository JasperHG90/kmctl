---
type: spike
title: Spike kmctl-follows-the-pin/3
description: does uvx --offline --from git+...@SHA with no cached copy fail fast, nonzero and without the network, and can kmctl tell that miss from the pinned command failing?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:50:24+00:00'
slug: kmctl-follows-the-pin
n: 3
outcome_written: true
---

# Spike kmctl-follows-the-pin/3

does uvx --offline --from git+...@SHA with no cached copy fail fast, nonzero and without the network, and can kmctl tell that miss from the pinned command failing?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin3/offline.sh
```

## Outcome

Exit 1 because the first empty-cache `uvx --offline --from git+...@<sha> kmctl --version` took 5268 ms (rc 1): `--offline` did not stop uv from running git (34 git execs) and fetching the source from the file:// clone; it failed only later, on `hatchling` missing from the cache. So `--offline` blocks registry downloads, not git fetches.
The later "unreachable clone" cases (43 ms, rc 1) are not clean misses: the first case had already put the git checkout in the cache. A follow-up spike retests with a fresh cache per case.
Warm (uv 0.13.0): `--offline` `--version` 202 ms rc 0, `briefing --format text` in an empty dir 192 ms rc 0, `kmctl nosuchcommand` rc 2, and `python -c 'sys.exit(N)'` gave rc 7, 1 and 2: uvx passes the child's exit code through unchanged, with no stderr of its own.
A cache miss exits 1, the same code a child can return; only the stderr text ("hint: Packages were unavailable because the network was disabled") tells them apart. `-q` and `uv tool run --offline` behave the same. Does not settle risk 1.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/offline.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin3/offline.sh`, which the command used
