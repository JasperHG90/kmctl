---
type: spike
title: Spike apm-hands-back/4
description: at user scope (apm install -g --target claude over git), does APM resolve the ./claude sub-package and write the hook to CLAUDE_CONFIG_DIR/settings.json and okf-bundle to CLAUDE_CONFIG_DIR/.claude.json; what does it leave over a kmctl-written user install; does uninstall -g clean up?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:58:36+00:00'
slug: apm-hands-back
n: 4
outcome_written: true
---

# Spike apm-hands-back/4

at user scope (apm install -g --target claude over git), does APM resolve the ./claude sub-package and write the hook to CLAUDE_CONFIG_DIR/settings.json and okf-bundle to CLAUDE_CONFIG_DIR/.claude.json; what does it leave over a kmctl-written user install; does uninstall -g clean up?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-user.sh
```

## Outcome

Exit 0 but not a result: the install failed (rc 1) because the spike's antigravity sub-package had an apm.yml and no .apm/ folder, which APM refuses ('missing the required .apm/ directory'). It shows APM resolves every sub-package even with --target claude, so each must be a valid package. Spike 5 reruns it with a valid one.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-user.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-user.sh`, which the command used
