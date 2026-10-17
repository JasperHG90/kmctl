---
type: spike
title: Spike antigravity-rules/1
description: does deleting APM's .agents/rules copies of kmctl's rules break a later apm install or apm uninstall?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:29:34+00:00'
slug: antigravity-rules
n: 1
outcome_written: true
---

# Spike antigravity-rules/1

does deleting APM's .agents/rules copies of kmctl's rules break a later apm install or apm uninstall?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-rules.sh
```

## Outcome

The risk does not hold. The command exits 1 only because its check counted two unrelated APM info lines ("Skipped inactive experimental resolver for target copilot-...") as skips. After deleting the four kmctl rule files APM deployed under .agents/rules/, apm install --target claude,antigravity exited 0, reported no "local files exist" skip, and wrote all four back. After deleting them again, apm uninstall of the kmctl entry exited 0, removed both packages and their hooks, deleted apm.lock.yaml, and left no file under .claude/skills, .claude/rules, .agents/skills or .agents/rules. So kmctl can delete those copies after every install, and a later install or uninstall still works.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-rules.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-rules.sh`, which the command used
