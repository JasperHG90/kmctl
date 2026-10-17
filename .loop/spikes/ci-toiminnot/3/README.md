---
type: spike
title: Spike ci-toiminnot/3
description: 'toiminnot''s pre_commit action (which runs prek) passes with prek_version 0.5.5: pip-installed prek 0.5.5 on Python 3.12 runs this repo''s hooks on every tracked file, with uv on PATH'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T18:03:30+00:00'
slug: ci-toiminnot
n: 3
outcome_written: false
---

# Spike ci-toiminnot/3

toiminnot's pre_commit action (which runs prek) passes with prek_version 0.5.5: pip-installed prek 0.5.5 on Python 3.12 runs this repo's hooks on every tracked file, with uv on PATH

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/runner.sh uv venv -q -p 3.12 /tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/home/venv && uv pip install -q -p /tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/home/venv prek==0.5.5 && /tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/home/venv/bin/prek run --show-diff-on-failure --files $(git ls-files); echo exit=$?; git status --short
```

## Outcome

Not written yet: `loopctl plan spike-note ci-toiminnot 3`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
