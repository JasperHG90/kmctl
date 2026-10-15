---
type: spike
title: Spike repo-uses-apm/1
description: does APM 0.33 install a jasperhg90/skills rule to .claude/rules/ with its front matter intact and a skill to .claude/skills/
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T17:49:01+00:00'
slug: repo-uses-apm
n: 1
outcome_written: true
---

# Spike repo-uses-apm/1

does APM 0.33 install a jasperhg90/skills rule to .claude/rules/ with its front matter intact and a skill to .claude/skills/

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/spike.sh
```

## Outcome

Not valid: script bug. `diff | head && echo byte-identical` took its exit code from `head`, so the run printed "byte-identical" under a real diff and exited 0 by mistake. Its stdout matches spike:repo-uses-apm/2, which has the fixed check and the outcome. Do not cite this one.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/spike.sh`, which the command used
