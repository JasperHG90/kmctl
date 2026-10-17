---
type: spike
title: Spike apm-hands-back/1
description: 'can one consumer entry {git, path: apm} pull per-harness sub-packages (targets claude / antigravity) by RELATIVE path, giving each harness only its own rules and hooks, okf MCP for both, and a clean uninstall?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:43:05+00:00'
slug: apm-hands-back
n: 1
outcome_written: true
---

# Spike apm-hands-back/1

can one consumer entry {git, path: apm} pull per-harness sub-packages (targets claude / antigravity) by RELATIVE path, giving each harness only its own rules and hooks, okf MCP for both, and a clean uninstall?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-subpkg.sh rel
```

## Outcome

Exit 0: the design works with relative sub-packages. A consumer apm.yml with one entry {git: URL, path: apm, ref: v0.0.1}, whose apm.yml lists ./claude (targets: [claude]) and ./antigravity (targets: [antigravity]) and declares okf-bundle under dependencies.mcp, installed with apm 0.33.0 --target claude,antigravity: .claude/rules/r.md got the Claude rule with paths, .agents/rules/r.md got the Antigravity rule as trigger: glob, globs: "**/docs/**, **/.okf/**" (from applyTo written with escaped commas), each harness got only its own SessionStart hook (.claude/settings.json, .agents/hooks.json), the shared skill reached both, and okf-bundle went to both .mcp.json and .agents/mcp_config.json. apm uninstall of the entry left no rule or skill file, emptied .agents/hooks.json to {} and took the hook out of settings.json. The git-URL variant was not needed.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-subpkg.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-subpkg.sh`, which the command used
