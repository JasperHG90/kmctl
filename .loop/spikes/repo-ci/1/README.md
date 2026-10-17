---
type: spike
title: Spike repo-ci/1
description: 'uv run pytest passes on a bare runner: fresh clone, empty HOME, no git identity, no kmctl/agy/claude/apm on PATH'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:38:08+00:00'
slug: repo-ci
n: 1
outcome_written: true
---

# Spike repo-ci/1

uv run pytest passes on a bare runner: fresh clone, empty HOME, no git identity, no kmctl/agy/claude/apm on PATH

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/runner.sh uv run pytest -q -p no:cacheprovider 2>&1 | tail -15
```

## Outcome

Holds. In a fresh clone of HEAD with an empty HOME, no git identity (GIT_CONFIG_GLOBAL=/dev/null) and only uv, uvx, git and system tools on PATH, `uv run pytest` passed: 696 passed, 8 deselected. The default suite needs no kmctl, agy, claude or APM install and no git identity, so a plain ubuntu runner with setup-uv runs it.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
