---
type: spike
title: Spike apm-distribution/2
description: does APM 0.33.0 deploy kmctl skills and agent from plugin/skills and plugin/agents as laid out, installed as a git subfolder package, with no copy (smart HTTP rerun)
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:11:10+00:00'
slug: apm-distribution
n: 2
outcome_written: true
---

# Spike apm-distribution/2

does APM 0.33.0 deploy kmctl skills and agent from plugin/skills and plugin/agents as laid out, installed as a git subfolder package, with no copy (smart HTTP rerun)

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike1-layout.sh
```

## Outcome

APM 0.33.0 installed kmctl's `plugin/` as it is, as a git subfolder package (`git: <repo>`, `path: plugin`, from a local smart-HTTP git server because APM rejects `file://` git URLs). It needs no apm.yml, because APM reads `plugin/.claude-plugin/plugin.json` as a Claude plugin. All 7 skill folders landed byte for byte at `.claude/skills/<name>/` (evals/ and references/ included), the agent at `.claude/agents/kmctl-auditor.md`, and the SessionStart hook in `.claude/settings.json` (APM adds `"matcher": "*"` and writes `.claude/apm-hooks.json`). The same holds with an apm.yml in `plugin/` that declares no dependencies.
Installing the repo root fails: "Not a valid APM package: no apm.yml, SKILL.md, hooks, or plugin structure". So the package is the `plugin/` subfolder, and no `.apm/` or root `skills/` copy is needed.
Settles risk 1: the layout needs no second copy. Limit: local git server, not GitHub. GitHub would use the same `path:` route, written `JasperHG90/Knowledge-management/plugin`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike1-layout.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike1-layout.sh`, which the command used
- `files/common.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh`, which the command used
- `files/githttp.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/githttp.py`, which the command used
