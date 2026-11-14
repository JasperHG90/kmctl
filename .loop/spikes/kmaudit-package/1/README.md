---
type: spike
title: Spike kmaudit-package/1
description: can one root pytest run collect kmctl tests/ and packages/kmaudit/tests/ (both with conftest.py, fixtures/audit_repo.py and duplicate test_*.py names) while kmctl keeps `from fixtures.audit_repo import`?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T11:34:30+00:00'
slug: kmaudit-package
n: 1
outcome_written: false
---

# Spike kmaudit-package/1

can one root pytest run collect kmctl tests/ and packages/kmaudit/tests/ (both with conftest.py, fixtures/audit_repo.py and duplicate test_*.py names) while kmctl keeps `from fixtures.audit_repo import`?

The command exited 0:

```
uv run python /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-pytest/layouts.py
```

## Outcome

Not written yet: `loopctl plan spike-note kmaudit-package 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/layouts.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-pytest/layouts.py`, which the command used
