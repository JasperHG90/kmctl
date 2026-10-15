---
type: spike
title: Spike plugin-install-verb/3
description: at project scope, does claude plugin install pull the cross-marketplace okf dependency, stay idempotent across reruns, and record both marketplaces and plugins in .claude/settings.json?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:23:40+00:00'
slug: plugin-install-verb
n: 3
outcome_written: true
---

# Spike plugin-install-verb/3

at project scope, does claude plugin install pull the cross-marketplace okf dependency, stay idempotent across reruns, and record both marketplaces and plugins in .claude/settings.json?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-plugin-install-project/project-scope-v2.sh
```

## Outcome

Project scope works. With claude 2.1.300, an isolated CLAUDE_CONFIG_DIR and a scratch git repo, `marketplace add --scope project` for both marketplaces (local folder + `scaccogatto/okf-skills`) then `plugin install tiny@spike-mkt --scope project` exited 0 with `(+ 1 dependency: okf)`; okf@scaccogatto 0.10.3 and tiny both listed at scope project. Nothing went to user settings.
Reruns: runs 2 and 3 exit 0 ("already on disk", "already installed"); settings content and the plugin list stay the same. The one change is cosmetic: run 2 rewrites `.claude/settings.json` with `enabledPlugins` moved above `extraKnownMarketplaces`, then the bytes hold steady from run 3 on. So the first rerun leaves a reorder-only diff in a committed file.
`.claude/settings.json` lists both marketplaces under `extraKnownMarketplaces` and both plugins under `enabledPlugins`, so a teammate's clone declares them. But a directory marketplace is saved as an absolute local path, so kmctl's staged folder will not resolve on a teammate's machine until they run `kmctl plugin install` themselves. A fresh config dir in the clone listed nothing from the CLI; the interactive trust prompt that installs declared marketplaces was not tested.
Settles risk 1: project scope can pull okf, so the plan does not have to fall back to user-scope-only.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/project-scope-v2.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-plugin-install-project/project-scope-v2.sh`, which the command used
