---
type: spike
title: Spike plugin-remove/3
description: after a claude,antigravity install, does apm uninstall of kmctl's entry leave no APM file and no lock, and does kmctl plugin install --harness claude then leave nothing under .agents/ from APM and claude whole?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:49:29+00:00'
slug: plugin-remove
n: 3
outcome_written: true
---

# Spike plugin-remove/3

after a claude,antigravity install, does apm uninstall of kmctl's entry leave no APM file and no lock, and does kmctl plugin install --harness claude then leave nothing under .agents/ from APM and claude whole?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove3.sh
```

## Outcome

Exit 0: the remove route works. In a scratch consumer installed for claude,antigravity (83 APM files), apm uninstall 127.0.0.1:PORT/o/kmctl/apm exited 0 and left no APM file under .claude/ or .agents/ and no lock; .agents/hooks.json stayed as {}. kmctl plugin install --harness claude from the same source then left no APM file under .agents/, all 11 skills under .claude/skills/, and no .agents/ path in the lock. One gap: apm.yml kept targets [claude, antigravity], because install adds targets and never drops one, so remove must take the removed harnesses out of targets: itself.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-remove3.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove3.sh`, which the command used
