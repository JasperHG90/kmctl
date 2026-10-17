---
type: spike
title: Spike plugin-remove/5
description: 'same as 4, not counting .claude/settings.json (kmctl edits it): does apm 0.33.0 uninstall github.com/OWNER/REPO/apm remove a GitHub-sourced kmctl entry and its files?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:52:47+00:00'
slug: plugin-remove
n: 5
outcome_written: true
---

# Spike plugin-remove/5

same as 4, not counting .claude/settings.json (kmctl edits it): does apm 0.33.0 uninstall github.com/OWNER/REPO/apm remove a GitHub-sourced kmctl entry and its files?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove4.sh
```

## Outcome

Exit 0: the GitHub form works. After an APM 0.33.0 install of kmctl's entry from https://github.com/JasperHG90/Knowledge-management.git (path apm), apm uninstall github.com/JasperHG90/Knowledge-management/apm exited 0, emptied dependencies.apm in apm.yml, removed its packages from apm_modules/ and left no file under .claude/ but settings.json, which kmctl edits itself; the dry run accepted JasperHG90/Knowledge-management/apm as well. So HOST/OWNER/REPO/apm, with host github.com when the lock names it, is the name to pass.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-remove4.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove4.sh`, which the command used
