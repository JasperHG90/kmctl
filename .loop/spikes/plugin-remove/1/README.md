---
type: spike
title: Spike plugin-remove/1
description: does apm 0.33.0 uninstall of the kmctl apm.yml entry remove every deployed .claude/.agents file, okf-skills (transitive), apm_modules and lock entries after kmctl plugin install --harness claude,antigravity
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:07:36+00:00'
slug: plugin-remove
n: 1
outcome_written: true
---

# Spike plugin-remove/1

does apm 0.33.0 uninstall of the kmctl apm.yml entry remove every deployed .claude/.agents file, okf-skills (transitive), apm_modules and lock entries after kmctl plugin install --harness claude,antigravity

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove-1/spike.sh
```

## Outcome

After `kmctl plugin install --harness claude,antigravity` from a local git server, `apm uninstall 127.0.0.1:PORT/o/kmctl/apm` (host/owner/repo/path, the apm.yml entry's identifier; the bare git URL is refused with "not found in apm.yml") exited 0. It removed kmctl and the transitive scaccogatto/okf-skills from apm_modules/, cleaned 65 + 40 deployed files, removed both integrated okf Stop hooks, deleted apm.lock.yaml outright and left apm.yml with `dependencies: apm: []` and `targets:` unchanged.
Nothing under .claude/skills, .claude/agents, .claude/rules, .claude/hooks, .agents/skills, .agents/rules or .agents/hooks remained; .claude/apm-hooks.json and .agents/apm-hooks.json went too.
The exit 1 comes from two leftovers: `.agents/hooks.json` emptied to `{}` rather than deleted, and `.agents/plugins/kmctl/` (written by kmctl, not APM; the plan already deletes it itself). Also left: an empty apm_modules/ folder and APM's `apm_modules/` line in .gitignore. kmctl's SessionStart hook in .claude/settings.json and okf-bundle in .mcp.json stay, as expected, since kmctl writes them.
Settles risk 1 for APM's files: remove need not delete skills, agents, rules, okf files or lock entries itself; at most it removes an `{}` .agents/hooks.json. Limits: one run, project scope only, and the GitHub-form identifier (owner/repo/apm) and the `o/kmctl/apm` name shown by `apm deps list` were not tried.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove-1/spike.sh`, which the command used
