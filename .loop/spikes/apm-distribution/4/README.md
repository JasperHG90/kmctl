---
type: spike
title: Spike apm-distribution/4
description: does APM 0.33.0 deploy the kmctl SessionStart hook and an okf-skills dependency declared in plugin/apm.yml to a consumer, and do kmctl --version and kmctl briefing run there
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:11:11+00:00'
slug: apm-distribution
n: 4
outcome_written: true
---

# Spike apm-distribution/4

does APM 0.33.0 deploy the kmctl SessionStart hook and an okf-skills dependency declared in plugin/apm.yml to a consumer, and do kmctl --version and kmctl briefing run there

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike3-hook-okf-cli.sh
```

## Outcome

A `plugin/apm.yml` declaring `scaccogatto/okf-skills#a8b96420` reached the consumer. It got okf's 4 skills (okf, validate, backfill, visualize), its 2 agents, and its Stop hook (script at `.claude/hooks/okf-skills/hooks/okf-stop-check.sh`). kmctl's SessionStart hook landed in `.claude/settings.json`. With kmctl on PATH (uv tool install), `kmctl --version` (0.1.0), `kmctl briefing --path <consumer>` and the deployed hook command all exit 0 and print the briefing.
The script exited 0, but it did not check the kmctl agent, and the agent is missing: `.claude/agents/` holds only okf's two. An apm.yml that declares dependencies makes APM treat `plugin/` as an APM-format package, which reads agents only from `.apm/agents/` (format_detection.py, agent_integrator.py). Also, okf's MCP server `bundle` is skipped as a transitive one, unless the consumer declares it again or passes `--trust-transitive-mcp`.
Does not settle risk 3 alone: deps in `plugin/apm.yml` lose the agent. See spike:apm-distribution/5.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike3-hook-okf-cli.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike3-hook-okf-cli.sh`, which the command used
- `files/common.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh`, which the command used
- `files/githttp.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/githttp.py`, which the command used
