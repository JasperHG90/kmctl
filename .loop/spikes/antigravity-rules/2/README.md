---
type: spike
title: Spike antigravity-rules/2
description: does deleting APM's .agents/rules copies of kmctl's rules break a later apm install or apm uninstall? (skip check counts only local-file skips)
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:30:07+00:00'
slug: antigravity-rules
n: 2
outcome_written: true
---

# Spike antigravity-rules/2

does deleting APM's .agents/rules copies of kmctl's rules break a later apm install or apm uninstall? (skip check counts only local-file skips)

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-rules.sh
```

## Outcome

The risk does not hold (exit 0). After deleting the four kmctl rule files APM deployed under .agents/rules/, apm install --target claude,antigravity exited 0 with no "local files exist" skip and wrote all four back; after deleting them again, apm uninstall of the kmctl entry exited 0 and left no file under .claude/skills, .claude/rules, .agents/skills or .agents/rules, and no lock. Spike 1 ran the same steps but its check also counted unrelated APM info lines as skips.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-rules.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-rules.sh`, which the command used
