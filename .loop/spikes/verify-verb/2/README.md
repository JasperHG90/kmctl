---
type: spike
title: Spike verify-verb/2
description: the briefing's state line names kmctl review due when concepts are due
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T21:21:30+00:00'
slug: verify-verb
n: 2
outcome_written: false
---

# Spike verify-verb/2

the briefing's state line names kmctl review due when concepts are due

The command exited 0:

```
sh -c uv run kmctl briefing | grep "^State:" | grep -E "[1-9][0-9]* concepts? due for review \(kmctl review due\)"
```

## Outcome

Not written yet: `loopctl plan spike-note verify-verb 2`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
