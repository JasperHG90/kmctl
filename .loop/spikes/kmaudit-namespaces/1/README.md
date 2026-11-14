---
type: spike
title: Spike kmaudit-namespaces/1
description: with Target.bundle pointed at a plain markdown folder (docs/, handbook/), which kmaudit code paths beyond resolve_target, the store path, EXCLUDE_DIRS and CLI help raise or give wrong results?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:06:14+00:00'
slug: kmaudit-namespaces
n: 1
outcome_written: false
---

# Spike kmaudit-namespaces/1

with Target.bundle pointed at a plain markdown folder (docs/, handbook/), which kmaudit code paths beyond resolve_target, the store path, EXCLUDE_DIRS and CLI help raise or give wrong results?

The command exited 1:

```
bash -c unset VIRTUAL_ENV; uv run --project /home/vscode/workspace python -I /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-ns/plain_folder.py
```

## Outcome

Not written yet: `loopctl plan spike-note kmaudit-namespaces 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/plain_folder.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-ns/plain_folder.py`, which the command used
