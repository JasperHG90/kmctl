---
type: spike
title: Spike kmctl-follows-the-pin/2
description: does a detached child (start_new_session, DEVNULL stdio) started by a session hook let the hook caller return at once, and still fill the cache after the hook exits or its process group is killed?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:48:17+00:00'
slug: kmctl-follows-the-pin
n: 2
outcome_written: true
---

# Spike kmctl-follows-the-pin/2

does a detached child (start_new_session, DEVNULL stdio) started by a session hook let the hook caller return at once, and still fill the cache after the hook exits or its process group is killed?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin2/spike.py
```

## Outcome

A parent that prints a line and starts a child with `Popen(..., stdin/stdout/stderr=DEVNULL, start_new_session=True)` returns to a pipe-reading caller in 0.03 s (`subprocess.run(capture_output=True)` and a bash `$(...)` capture alike), and the child still writes the cache about 3.1 s later, after parent and caller have exited.
Killing the parent's process group after it exits (`os.killpg`) finds the group already empty: the child sits in its own session and filled the cache at 3.09 s.
A real Claude Code SessionStart hook (`claude -p --model haiku --settings`, child sleeping 25 s) returned in 8.8 s with the cache not yet written, and the cache appeared at 26 s, so Claude Code neither waits for the child nor kills it.
Settles risk 2 for Linux and Claude Code. Not tested: the OpenCode plugin or macOS/Windows.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-pin2/spike.py`, which the command used
