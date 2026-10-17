---
type: spike
title: Spike apm-hands-back/5
description: 'same as 4 with a valid antigravity sub-package: at user scope, does apm install -g --target claude write the hook to CLAUDE_CONFIG_DIR/settings.json and okf-bundle to CLAUDE_CONFIG_DIR/.claude.json; over a kmctl-written user install, and after uninstall -g?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:58:37+00:00'
slug: apm-hands-back
n: 5
outcome_written: true
---

# Spike apm-hands-back/5

same as 4 with a valid antigravity sub-package: at user scope, does apm install -g --target claude write the hook to CLAUDE_CONFIG_DIR/settings.json and okf-bundle to CLAUDE_CONFIG_DIR/.claude.json; over a kmctl-written user install, and after uninstall -g?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-user.sh
```

## Outcome

Exit 0 (observation): user scope works like project scope. With ~/.apm/apm.yml naming the split package over git, apm 0.33.0 install -g --target claude resolved ./claude and ./antigravity (the latter skipped for its target), wrote the shared skill and the SessionStart hook into $CLAUDE_CONFIG_DIR (recorded in its apm-hooks.json) and reported okf-bundle. Over a user install today's kmctl wrote (kmctl's hook group with no matcher in settings.json, an okf-bundle at an older pin in $CLAUDE_CONFIG_DIR/.claude.json): two kmctl hooks and the stale okf-bundle stayed. After removing kmctl's unrecorded hook group and the stale okf-bundle, a second install -g left exactly one hook, recorded by APM, and the package's okf-bundle in .claude.json; another server stayed. apm uninstall -g then removed the hook and the skill but LEFT okf-bundle in .claude.json, unlike project scope, where uninstall emptied okf-bundle from .mcp.json and .agents/mcp_config.json (spike 1's consumer).

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-user.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-user.sh`, which the command used
