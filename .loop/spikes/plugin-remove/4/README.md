---
type: spike
title: Spike plugin-remove/4
description: after an install from https://github.com/JasperHG90/Knowledge-management.git (path apm), does apm 0.33.0 uninstall accept github.com/OWNER/REPO/apm, and does OWNER/REPO/apm work too?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:52:46+00:00'
slug: plugin-remove
n: 4
outcome_written: true
---

# Spike plugin-remove/4

after an install from https://github.com/JasperHG90/Knowledge-management.git (path apm), does apm 0.33.0 uninstall accept github.com/OWNER/REPO/apm, and does OWNER/REPO/apm work too?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove4.sh
```

## Outcome

Exit 1 only because the check counted .claude/settings.json, which APM leaves after taking its hook out (kmctl edits that file itself). After installing {git: https://github.com/JasperHG90/Knowledge-management.git, path: apm, ref: v0.3.0} with APM 0.33.0 (lock host github.com, repo_url JasperHG90/Knowledge-management), apm uninstall --dry-run accepted both github.com/JasperHG90/Knowledge-management/apm and JasperHG90/Knowledge-management/apm, and the real uninstall of the github.com form exited 0, removed the entry from apm.yml and its packages from apm_modules/. Note: the v0.3.0 tag on GitHub still has the old plugin/ layout, so its lock also shows an orphaned .../plugin package, which the uninstall removed too.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-remove4.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove4.sh`, which the command used
