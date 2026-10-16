---
type: spike
title: Spike apm-only-install/6
description: 'does apm install remove an ADR 0013 v0.3.0 package (files and SessionStart hook) when apm.yml swaps it for the new {git, path: apm} entry, and keep exactly one kmctl hook across re-installs?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev173+ga4f6ce93a.d20261016
  at: '2026-10-16T20:25:58+00:00'
slug: apm-only-install
n: 6
outcome_written: false
---

# Spike apm-only-install/6

does apm install remove an ADR 0013 v0.3.0 package (files and SessionStart hook) when apm.yml swaps it for the new {git, path: apm} entry, and keep exactly one kmctl hook across re-installs?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate/p1.sh
```

## Outcome

Not written yet: `loopctl plan spike-note apm-only-install 6`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/p1.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate/p1.sh`, which the command used
