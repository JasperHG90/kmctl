---
type: spike
title: Spike apm-only-install/6
description: 'does apm install remove an ADR 0013 v0.3.0 package (files and SessionStart hook) when apm.yml swaps it for the new {git, path: apm} entry, and keep exactly one kmctl hook across re-installs?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev173+ga4f6ce93a.d20261016
  at: '2026-10-16T20:26:10+00:00'
slug: apm-only-install
n: 6
outcome_written: true
---

# Spike apm-only-install/6

does apm install remove an ADR 0013 v0.3.0 package (files and SessionStart hook) when apm.yml swaps it for the new {git, path: apm} entry, and keep exactly one kmctl hook across re-installs?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate/p1.sh
```

## Outcome

Answers plan review finding p1 (ADR 0013 users), under risk 4. Old install of `JasperHG90/Knowledge-management/apm#v0.3.0` from GitHub, then the apm.yml entry swapped for `{git: <served new tree>, path: apm}` plus a plain kmctl SessionStart entry, APM 0.33.0.
- Swap then `apm install` (exit 0): the new files land (7 skills and agent byte for byte, 4 rules, okf skills), the old deps leave the lock, and no old-only file stays on disk (the 30 old paths are all re-owned by the new package). But the old hook stays. APM marks it `_apm_source: jasperhg90/knowledge-management/plugin` in `.claude/apm-hooks.json`, not in settings.json. `settings.json` then has 2 kmctl SessionStart entries, which a second install keeps. `apm prune` (it removed 2 orphaned packages) and another install leave the old hook in place too.
- `apm uninstall JasperHG90/Knowledge-management/apm` before the swap works (exit 0). It removes the apm.yml entry, both old deps and the transitive okf, cleans 29 plus 21 files, and prints `Cleaned up 1 integrated hooks`. That leaves 0 SessionStart entries. After the swap and `apm install` there is exactly 1 kmctl entry (kmctl's plain one), which a second install keeps. The spike exits 0 on this route.
Settles finding p1 only if the plan runs `apm uninstall <old entry>` before rewriting apm.yml. Swapping the entry, or pruning, leaves a duplicate briefing hook. Limit: between uninstall and install the repo briefly has no skills. Tested on project scope only; the real ~/.claude was untouched.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/p1.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate/p1.sh`, which the command used
