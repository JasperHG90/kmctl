---
type: spike
title: Spike apm-distribution/5
description: with plugin/ left without an apm.yml, does a meta package apm/apm.yml (git parent plus okf-skills) or a consumer listing both get kmctl skills, agent, hook, okf skills and a working kmctl into an APM 0.33.0 consumer
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:11:12+00:00'
slug: apm-distribution
n: 5
outcome_written: true
---

# Spike apm-distribution/5

with plugin/ left without an apm.yml, does a meta package apm/apm.yml (git parent plus okf-skills) or a consumer listing both get kmctl skills, agent, hook, okf skills and a working kmctl into an APM 0.33.0 consumer

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike5-okf-routes.sh
```

## Outcome

With `plugin/` unchanged (no apm.yml in it), both routes got everything into an APM 0.33.0 consumer. That is all 7 kmctl skills and the agent byte for byte, kmctl's SessionStart hook in `.claude/settings.json`, and okf's 4 skills, 2 agents and Stop hook.
M: a meta package `apm/apm.yml` in the same repo depends on `{git: parent, path: plugin}` and `scaccogatto/okf-skills#a8b96420`. The consumer installs `path: apm`, a single install line. okf's MCP server `bundle` is skipped as transitive.
D: the consumer lists `path: plugin` and `scaccogatto/okf-skills` itself. okf's MCP server is configured.
From the M consumer, with kmctl on PATH, `kmctl --version`, `kmctl briefing --path` and the deployed hook command exit 0 and print the briefing.
Settles risk 3, leaving the operator's call. Limits: local git server for the kmctl repo; okf came from GitHub at a8b96420; APM warns about hidden characters in one okf-skills file.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike5-okf-routes.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike5-okf-routes.sh`, which the command used
- `files/common.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh`, which the command used
- `files/githttp.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/githttp.py`, which the command used
