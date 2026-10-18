---
type: spike
title: Spike kmctl-follows-the-pin/2
description: does a detached child (start_new_session, DEVNULL stdio) started by a session hook let the hook caller return at once, and still fill the cache after the hook exits or its process group is killed?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:48:06+00:00'
slug: kmctl-follows-the-pin
n: 2
outcome_written: false
---

# Spike kmctl-follows-the-pin/2

does a detached child (start_new_session, DEVNULL stdio) started by a session hook let the hook caller return at once, and still fill the cache after the hook exits or its process group is killed?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin2/spike.py
```

## Outcome

Not written yet: `loopctl plan spike-note kmctl-follows-the-pin 2`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin2/spike.py`, which the command used
