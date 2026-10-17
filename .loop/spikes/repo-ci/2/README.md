---
type: spike
title: Spike repo-ci/2
description: uvx prek@0.5.5 run --all-files passes on a bare runner and leaves the clone unchanged
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:38:09+00:00'
slug: repo-ci
n: 2
outcome_written: true
---

# Spike repo-ci/2

uvx prek@0.5.5 run --all-files passes on a bare runner and leaves the clone unchanged

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/repo-ci/runner.sh uvx prek@0.5.5 run --all-files; echo prek-exit=$?; git status --short
```

## Outcome

Holds. In the same bare clone, `uvx prek@0.5.5 run --all-files` ran both local hooks (generate the Antigravity rules, kmctl check --fix), both passed, prek exited 0 and git status was clean afterwards. The hooks use `uv run`, so the job needs setup-uv and nothing else.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
