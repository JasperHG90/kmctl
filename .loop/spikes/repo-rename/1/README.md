---
type: spike
title: Spike repo-rename/1
description: APM installs kmctl's package from https://github.com/JasperHG90/kmctl.git and its lock names it kmctl at virtual_path apm, the name and path kmctl_package matches, not the URL
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:49:08+00:00'
slug: repo-rename
n: 1
outcome_written: true
---

# Spike repo-rename/1

APM installs kmctl's package from https://github.com/JasperHG90/kmctl.git and its lock names it kmctl at virtual_path apm, the name and path kmctl_package matches, not the URL

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/rename/spike.sh
```

## Outcome

Holds. The real APM 0.33.0 installed {git: https://github.com/JasperHG90/kmctl.git, path: apm, ref: main} into an empty project. The lock names the package kmctl at virtual_path apm (repo_url jasperhg90/kmctl), with kmctl-claude and kmctl-antigravity at apm/claude and apm/antigravity from the same repo_url. kmctl_package matches name and virtual_path, not the URL, so a lock from either URL is found the same way.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
