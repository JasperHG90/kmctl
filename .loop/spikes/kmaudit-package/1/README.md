---
type: spike
title: Spike kmaudit-package/1
description: can one root pytest run collect kmctl tests/ and packages/kmaudit/tests/ (both with conftest.py, fixtures/audit_repo.py and duplicate test_*.py names) while kmctl keeps `from fixtures.audit_repo import`?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T11:34:43+00:00'
slug: kmaudit-package
n: 1
outcome_written: true
---

# Spike kmaudit-package/1

can one root pytest run collect kmctl tests/ and packages/kmaudit/tests/ (both with conftest.py, fixtures/audit_repo.py and duplicate test_*.py names) while kmctl keeps `from fixtures.audit_repo import`?

The command exited 0:

```
uv run python /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-pytest/layouts.py
```

## Outcome

On a dummy copy of the layout (pytest 9.1.1, kmctl's pyproject pytest config, default prepend mode, no testpaths), one root run collects both trees cleanly if `packages/kmaudit/tests/` gets an `__init__.py` (plus one in its `fixtures/`) and kmaudit imports its fixtures relatively (`from .fixtures.audit_repo import ...`). That works with duplicate `conftest.py`, `fixtures/audit_repo.py` and `test_*.py` names, both with bare `pytest` and with both paths named. kmctl's tree and its `from fixtures.audit_repo import` stay as they are.
Ruled out: keeping kmaudit's tests rootless gives "import file mismatch" on any duplicate test basename, and a second `fixtures` package is shadowed by kmctl's, so kmaudit tests silently get kmctl's fixtures (3 of 5 failed). Renaming to `kmaudit_fixtures` plus unique test names also works. `--import-mode=importlib` alone breaks kmctl's `fixtures` import; it only works if `pythonpath` also lists both tests dirs.
Settles risk 1: no separate gate and no importlib switch needed. The cost is two `__init__.py` files and relative imports in kmaudit's tests. Limit: dummy tests only, not the real 1400-test suite.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/layouts.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-pytest/layouts.py`, which the command used
