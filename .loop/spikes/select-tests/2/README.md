---
type: spike
title: Spike select-tests/2
description: do default-suite tests that run kmctl as a separate process, from a built or installed copy, leave no src/ lines in a per-test coverage map?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T11:48:24+00:00'
slug: select-tests
n: 2
outcome_written: true
---

# Spike select-tests/2

do default-suite tests that run kmctl as a separate process, from a built or installed copy, leave no src/ lines in a per-test coverage map?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/wt/.venv/bin/python -I /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/risk2_subprocess.py /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/data/map.json /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/data/procs.json
```

## Outcome

The risk does not hold for the default suite. Coverage measured no kmctl file outside the worktree's `src/` (0 files, 0 tests). The static scan found 23 default tests in 4 files (test_action, test_pin, test_antigravity, test_summary) that run kmctl in another process. All 23 have src/ lines in the map (about 1950 to 2570 each) and at least one measured subprocess. At runtime, 30 tests started 37 kmctl subprocesses, and every one of those tests ran this tree's src/ there. Each such process runs this checkout's code through the venv's `kmctl` or a `python -c "from kmctl import main"` shim, with COV_TEST_ID set.
Only 3 default tests have no src/ line and build a wheel or sdist: the two version-source tests in test_release and test_apm_package's wheel test. They run no kmctl code and check the build and the `apm/` and `pyproject.toml` inputs, which already force a full run. The tests that run kmctl from an installed copy (uvx prek, a smoke-tested wheel, the starter bootstrap) are all marked integration, so the tests gate never runs them.
Settles risk 2. Limit: the static scan follows helpers within a file and conftest only. The runtime count (30 tests) covers what it misses.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/risk2_subprocess.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-select/risk2_subprocess.py`, which the command used
