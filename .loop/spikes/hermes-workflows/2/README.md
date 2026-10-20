---
type: spike
title: Spike hermes-workflows/2
description: 'Risk 1: do the copied okf skill, prompts and Hermes workflows pass every prek hook?'
tags:
- spike
generated:
  by: process:loopctl/2.2.2.dev82+g0ed6ce5f1.d20261019
  at: '2026-10-20T08:31:19+00:00'
slug: hermes-workflows
n: 2
outcome_written: true
---

# Spike hermes-workflows/2

Risk 1: do the copied okf skill, prompts and Hermes workflows pass every prek hook?

The command exited 0:

```
python3 /home/vscode/scratch/hermes-spike/check_hooks.py
```

## Outcome

The risk does not hold. In a throwaway worktree of HEAD, the script copied
the workspace okf skill (SKILL.md and references/), both prompts and both
Hermes workflows into .github/, staged them, and `uvx prek run --all-files`
exited 0: every hook passed, including kmctl check --fix, ruff and
okf validate --strict. The copy commits as it is.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/check_hooks.py`: a copy of `/home/vscode/scratch/hermes-spike/check_hooks.py`, which the command used
