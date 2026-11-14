---
type: spike
title: Spike kmctl-to-packages/1
description: with kmctl in packages/kmctl and its version file and force-included skills, agents and rules at ../../apm, do uv build (sdist then wheel), uv build --wheel, a git+file subdirectory install and a git-archive folder install all give a wheel or install at apm.yml version that check_wheel and smoke_wheel accept, and if not which hatch setting fixes it?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:33:28+00:00'
slug: kmctl-to-packages
n: 1
outcome_written: true
---

# Spike kmctl-to-packages/1

with kmctl in packages/kmctl and its version file and force-included skills, agents and rules at ../../apm, do uv build (sdist then wheel), uv build --wheel, a git+file subdirectory install and a git-archive folder install all give a wheel or install at apm.yml version that check_wheel and smoke_wheel accept, and if not which hatch setting fixes it?

The command exited 1:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/builds.py
```

## Outcome

The plan's config (version regex on `../../apm/apm.yml`, wheel force-includes from `../../apm/...`) passes 3 of 4 builds with apm.yml bumped to 0.99.0: `uv build --wheel --package kmctl` (check_wheel and smoke_wheel exit 0), the `git+file://...@v0.99.0#subdirectory=packages/kmctl` install and the git-archive folder install (both print `kmctl 0.99.0` and hold `_skills`, `_agents`, `_rules`). Plain `uv build --package kmctl` fails: the wheel built from the extracted sdist raises "Forced include not found" for `../../apm/.apm/agents`. The version itself is fine from the sdist (hatchling reads PKG-INFO).
Ruled out: adding an sdist force-include of the same sources into `apm/` does not help, because the wheel config still points at `../../apm`.
Two fixes pass where needed. A committed symlink `packages/kmctl/apm -> ../../apm`, with every path written as `apm/...`, passes all 4 unchanged scripts (its sdist carries all 43 apm/ files). A custom hatch build hook (`hatch_build.py`: use `../../apm` if it exists, else the sdist's `apm/`) plus the sdist force-include gives a correct wheel both ways (smoke_wheel 0, all 3 folders present). But check_wheel fails with KeyError 'force-include' because the wheel table is gone, so the script would have to read the hook's table.
Settles risk 1: no, the risk is real for the plan as written. The plan needs the symlink (or the hook plus a check_wheel change), or the release must build with `--wheel` and stop shipping an sdist. Limits: uv 0.13.7 on Linux; a local file:// remote, with `git archive` standing in for the action download; symlinks not tried on Windows.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/builds.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/builds.py`, which the command used
- `files/restructure.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/restructure.py`, which the command used
- `files/hatch_build.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/hatch_build.py`, which the command used
