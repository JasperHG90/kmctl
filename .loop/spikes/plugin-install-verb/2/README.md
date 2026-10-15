---
type: spike
title: Spike plugin-install-verb/2
description: at project scope, does claude plugin install pull the cross-marketplace okf dependency, stay idempotent, and record both marketplaces and plugins in .claude/settings.json?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:23:02+00:00'
slug: plugin-install-verb
n: 2
outcome_written: true
---

# Spike plugin-install-verb/2

at project scope, does claude plugin install pull the cross-marketplace okf dependency, stay idempotent, and record both marketplaces and plugins in .claude/settings.json?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-plugin-install-project/project-scope.sh
```

## Outcome

With claude 2.1.300, an isolated CLAUDE_CONFIG_DIR and a scratch git repo, `marketplace add --scope project` for both marketplaces then `plugin install tiny@spike-mkt --scope project` exited 0 with `(+ 1 dependency: okf)`; `plugin list --json` showed okf@scaccogatto 0.10.3 and tiny both at scope project.
`.claude/settings.json` got both marketplaces under `extraKnownMarketplaces` and both plugins under `enabledPlugins`; nothing was written to user settings.
Exit 1 only because the check compared bytes: the second run reported "already on disk" / "already installed" but rewrote settings.json with `enabledPlugins` moved above `extraKnownMarketplaces` (same content). Superseded by spike 3, which compares content and adds a third run.
A clone opened with a fresh config dir listed no marketplaces or plugins from the CLI; the trust prompt in an interactive session was not tested.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/project-scope.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-plugin-install-project/project-scope.sh`, which the command used
