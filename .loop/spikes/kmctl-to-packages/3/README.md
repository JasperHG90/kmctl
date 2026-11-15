---
type: spike
title: Spike kmctl-to-packages/3
description: with packages/kmctl/hatch_build.py (../../apm in a checkout, else the sdist's apm/), an sdist force-include of skills, agents and instructions, and check_wheel reading the hook's table, do uv build, uv build --wheel, a git+file subdirectory install and a git-archive folder install all pass at apm.yml's version?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:47:49+00:00'
slug: kmctl-to-packages
n: 3
outcome_written: true
---

# Spike kmctl-to-packages/3

with packages/kmctl/hatch_build.py (../../apm in a checkout, else the sdist's apm/), an sdist force-include of skills, agents and instructions, and check_wheel reading the hook's table, do uv build, uv build --wheel, a git+file subdirectory install and a git-archive folder install all pass at apm.yml's version?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/builds_confirm.py
```

## Outcome

With the plan's revised config (`packages/kmctl/hatch_build.py` using `../../apm` in a checkout and the sdist's `apm/` otherwise; an sdist force-include of only `.apm/skills`, `.apm/agents` and `claude/.apm/instructions`, with no apm.yml; and `scripts/check_wheel.py` reading the hook's `apm-include` table when the wheel has no force-include table), all 4 builds pass with apm.yml bumped to 0.99.0. (a) `uv build --package kmctl` builds an sdist holding 34 apm/ files, then a wheel from it. (b) `uv build --wheel --package kmctl` builds the wheel directly. Both wheels hold `_skills`, `_agents` and `_rules`, and check_wheel and smoke_wheel exit 0 on each. (c) The `git+file://...@v0.99.0#subdirectory=packages/kmctl` install and (d) the git-archive folder install both print `kmctl 0.99.0` and hold all three folders.
This rules out spike 1's "Forced include not found" failure on the sdist path. It also shows the sdist does not need a copy of apm.yml, because hatchling reads the version from PKG-INFO.
Settles risk 1: yes, for the plan as revised. Limits: uv 0.13.7 on Linux; a local file:// remote, with `git archive` standing in for the action download; the check_wheel change tested is the patch in `builds_confirm.py`, not the final code.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/builds_confirm.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/builds_confirm.py`, which the command used
- `files/builds.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/builds.py`, which the command used
- `files/restructure.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/restructure.py`, which the command used
- `files/hatch_build.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p/hatch_build.py`, which the command used
