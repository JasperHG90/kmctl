---
type: spike
title: Spike init-claude-md-always/2
description: on the toml-parser and job-queue scaffolds, does an agent record more decisions and architecture pages with the new kmctl init and plugin than with kmctl before init-seeds-the-habit
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T17:24:36+00:00'
slug: init-claude-md-always
n: 2
outcome_written: true
---

# Spike init-claude-md-always/2

on the toml-parser and job-queue scaffolds, does an agent record more decisions and architecture pages with the new kmctl init and plugin than with kmctl before init-seeds-the-habit

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/smoke-scenarios/driver.py
```

## Outcome

Mismeasured, superseded by spike 3. The driver measured only the main checkout, but 4 of 8 agents did the milestone in a git worktree they made (AGENTS.md says "Work in a worktree"), so those rows read 0 and "no tests ran". Re-measured by hand in those worktrees: NEW decisions 2/2/1/2 (mean 1.75), one architecture page in each run (mean 1.0), tests pass 4/4; OLD decisions 0 and architecture pages 0 in all 4, tests pass 4/4. The exit 0 (NEW above OLD on both) holds after the fix. Runs took 36 to 128 s and $0.34 to $0.72, because the first milestone (Phase 0) is a smoke test.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/driver.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/smoke-scenarios/driver.py`, which the command used
