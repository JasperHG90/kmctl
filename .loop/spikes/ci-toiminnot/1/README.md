---
type: spike
title: Spike ci-toiminnot/1
description: pre-commit 4.2.0 (what toiminnot's prek action runs) passes this repo's hooks on every tracked file, given uv on PATH, on a bare runner
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:58:50+00:00'
slug: ci-toiminnot
n: 1
outcome_written: true
---

# Spike ci-toiminnot/1

pre-commit 4.2.0 (what toiminnot's prek action runs) passes this repo's hooks on every tracked file, given uv on PATH, on a bare runner

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/runner.sh uvx --python 3.12 pre-commit==4.2.0 run --show-diff-on-failure --files $(git ls-files); echo exit=$?; git status --short
```

## Outcome

Holds. In a fresh clone with an empty HOME, no git identity and only uv, uvx, git and system tools on PATH, `pre-commit==4.2.0 run --show-diff-on-failure --files $(git ls-files)` (what toiminnot prek action v1.3.0 runs) ran both local hooks; both passed, exit 0, tree clean. The hooks call `uv run`, so the job must put uv on PATH before the action: the action installs only Python and pre-commit.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
