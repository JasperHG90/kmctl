---
type: spike
title: Spike apm-distribution/1
description: does APM 0.33.0 deploy kmctl skills and agent from plugin/skills and plugin/agents as laid out, installed as a git subfolder package, with no copy
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:11:09+00:00'
slug: apm-distribution
n: 1
outcome_written: true
---

# Spike apm-distribution/1

does APM 0.33.0 deploy kmctl skills and agent from plugin/skills and plugin/agents as laid out, installed as a git subfolder package, with no copy

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike1-layout.sh
```

## Outcome

Superseded by spike:apm-distribution/2. Served the source repo over dumb HTTP, where APM 0.33.0's shallow clone fails ("dumb http transport does not support shallow capabilities"). So case A (install the repo root) failed on transport, not on layout, and does not count. Cases B and C match spike 2: with `path: plugin`, all 7 skills and the agent deploy byte for byte. Use spike 2 for risk 1.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike1-layout.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike1-layout.sh`, which the command used
- `files/common.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh`, which the command used
