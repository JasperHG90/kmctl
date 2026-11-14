---
type: spike
title: Spike kmctl-to-packages/4
description: with the root at [tool.uv] package = false, members packages/*, -p pytester in the root pytest addopts and the moved conftest's pytest_plugins line removed, does one root pytest -m 'not integration' --collect-only select exactly 1407 tests with no collection errors?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:48:40+00:00'
slug: kmctl-to-packages
n: 4
outcome_written: true
---

# Spike kmctl-to-packages/4

with the root at [tool.uv] package = false, members packages/*, -p pytester in the root pytest addopts and the moved conftest's pytest_plugins line removed, does one root pytest -m 'not integration' --collect-only select exactly 1407 tests with no collection errors?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/collect_confirm.py
```

## Outcome

With the root at `[tool.uv] package = false` and `members = ["packages/*"]`, plus the O2 test split and its path fixes, `"-p", "pytester"` in the root pytest addopts and the moved conftest's `pytest_plugins` line removed: `uv sync` exits 0, and one root `uv run pytest -m "not integration" --collect-only -q` exits 0 with "1407/1421 tests collected (14 deselected)" and no ERROR lines. The 1407 split as 876 in packages/kmctl, 276 in tests/ and 255 in packages/kmaudit.
This rules out spike 2's collection error ("Defining 'pytest_plugins' in a non-top-level conftest") and any drop in the selected count.
Settles risk 3: yes, for the plan as revised. Limit: this checks collection only, not a full test run; spike 2's full run still had 31 failures from hard-coded root paths that O2 must rewrite.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/collect_confirm.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/collect_confirm.py`, which the command used
- `files/restructure.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/restructure.py`, which the command used
