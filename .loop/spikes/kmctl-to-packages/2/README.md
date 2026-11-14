---
type: spike
title: Spike kmctl-to-packages/2
description: with a package = false uv workspace root (members packages/*), does uv sync install kmctl and kmaudit editable, does uv run kmctl --version work, and does one root pytest collect tests/, a rootless packages/kmctl/tests and kmaudit package tests without conftest clashes, selecting the same count as today?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:44:23+00:00'
slug: kmctl-to-packages
n: 2
outcome_written: false
---

# Spike kmctl-to-packages/2

with a package = false uv workspace root (members packages/*), does uv sync install kmctl and kmaudit editable, does uv run kmctl --version work, and does one root pytest collect tests/, a rootless packages/kmctl/tests and kmaudit package tests without conftest clashes, selecting the same count as today?

The command exited 1:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/workspace_tests.py
```

## Outcome

Not written yet: `loopctl plan spike-note kmctl-to-packages 2`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/workspace_tests.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/workspace_tests.py`, which the command used
- `files/restructure.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/restructure.py`, which the command used
- `files/conftest_probe.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/conftest_probe.py`, which the command used
