---
type: spike
title: Spike kmctl-to-packages/2
description: with a package = false uv workspace root (members packages/*), does uv sync install kmctl and kmaudit editable, does uv run kmctl --version work, and does one root pytest collect tests/, a rootless packages/kmctl/tests and kmaudit package tests without conftest clashes, selecting the same count as today?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:44:41+00:00'
slug: kmctl-to-packages
n: 2
outcome_written: true
---

# Spike kmctl-to-packages/2

with a package = false uv workspace root (members packages/*), does uv sync install kmctl and kmaudit editable, does uv run kmctl --version work, and does one root pytest collect tests/, a rootless packages/kmctl/tests and kmaudit package tests without conftest clashes, selecting the same count as today?

The command exited 1:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/workspace_tests.py
```

## Outcome

With the root at `[tool.uv] package = false`, `members = ["packages/*"]` and both members in the dev group, `uv sync` installs kmctl and kmaudit editable (direct_url.json says `editable: true`), and `KMCTL_PINNED=1 uv run kmctl --version` prints `kmctl 0.12.1`, matching apm.yml. But the O2 split as written collects only 531 of the 1407 tests (baseline at 546f8011): the whole `packages/kmctl/tests` tree errors with "Defining 'pytest_plugins' in a non-top-level conftest", from the moved conftest's `pytest_plugins = ("pytester",)`.
Any one of three one-line fixes brings back exactly 1407 selected (876 kmctl, 276 root, 255 kmaudit) with no collection errors: `"-p", "pytester"` in the root addopts (dropping the conftest line), moving that line into the root `tests/conftest.py`, or `testpaths` listing the three trees. A probe found 0 of 27 functions imported from `conftest`, `fixtures.*` or `test_*` coming from the wrong tree. So two rootless conftests do not clash, and kmctl's tests do not need to become a package.
The run also applied path fixes the plan understates: the parents[2] fallbacks become parents[4], and 24 moved test files use `Path(__file__).resolve().parents[1]` as the repo root, which becomes parents[3]. Even then, a full run with the addopts fix had 31 failures, none naming a missing fixture or import. The ones read come from hard-coded `ROOT / "tests" / ...` and root `pyproject.toml` paths (test_network_retry, test_check_wheel, test_release), which O2 must also rewrite.
Settles risk 3: no, the risk is real as written (pytest_plugins), but the fix is one line and the split stays. Note: O2's "888 under packages/kmctl/tests" counts tests held; 876 are selected.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/workspace_tests.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/workspace_tests.py`, which the command used
- `files/restructure.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/restructure.py`, which the command used
- `files/conftest_probe.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/conftest_probe.py`, which the command used
