---
type: spike
title: Spike select-tests/1
description: how much of the default suite would a per-test coverage selector run per commit here, and how often would apm/, conftest, fixtures, pyproject.toml or uv.lock force a full run?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T11:48:23+00:00'
slug: select-tests
n: 1
outcome_written: true
---

# Spike select-tests/1

how much of the default suite would a per-test coverage selector run per commit here, and how often would apm/, conftest, fixtures, pyproject.toml or uv.lock force a full run?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/wt/.venv/bin/python -I /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/risk1_saving.py /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/data/map.json /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/upstream 40
```

## Outcome

The risk is real. The selector's own `select()` (loop-engineering-harness@9bc19cb6, this repo's fallback rules) ran against a per-test map of the 1406 default tests, recorded at 4453fa8e. Across the last 40 non-merge commits that touch a path outside `.loop/`, 15 fell back to a full run: 9 for `apm/`, 3 for `src/kmctl/claims/ui.html` (a non-Python file in the package), 2 for `pyproject.toml` and 1 for a conftest. The other 25 ran a median of 1055 tests (min 494, max 1182). The median commit runs 83% of the suite, and the mean is 80%.
The selection has two floors. 494 tests (35%) hit no kmctl line, so every run includes them: test_help 62, test_agent 55, tests/scripts 138. And 21 test files build their own `.okf/` and name ".okf", so any `.okf/` change runs all of them. With `.okf` dropped from the readable roots, the 25 selected runs fall to a median of 496 tests.
Settles risk 1: with the rules as planned, the saving is small. Limits: each old commit's diff was carried to the 4453fa8e map through `git diff C^ BASE`. The map is at /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/data/map.json (scratch, not kept). The full record run with coverage in every process took 125 s, not 17 min.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/risk1_saving.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/risk1_saving.py`, which the command used
