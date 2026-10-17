---
type: spike
title: Spike ci-toiminnot/2
description: toiminnot's pytest command, with markers 'not integration' and directory tests, passes on a bare runner and runs no integration test
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:58:51+00:00'
slug: ci-toiminnot
n: 2
outcome_written: true
---

# Spike ci-toiminnot/2

toiminnot's pytest command, with markers 'not integration' and directory tests, passes on a bare runner and runs no integration test

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/runner.sh uv sync -q --all-extras --all-groups && uv run pytest tests -v -m 'not integration' --color=no --tb=short 2>&1 | tail -3
```

## Outcome

Holds. In the same bare clone, toiminnot pytest action v1.3.0 commands (`uv sync --all-extras --all-groups`, then `uv run pytest tests -v -m "not integration" --tb=short`) gave 703 passed, 8 deselected. With the action default markers (empty) the command becomes `-m ""`, which clears the filter and would run the integration tier too, so the job must pass markers: not integration.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
