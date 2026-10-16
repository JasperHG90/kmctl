---
type: spike
title: Spike apm-only-install/4
description: does apm install print a greppable skip line naming a hand-made skill it will not overwrite, and does --force replace it?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:20:06+00:00'
slug: apm-only-install
n: 4
outcome_written: true
---

# Spike apm-only-install/4

does apm install print a greppable skip line naming a hand-made skill it will not overwrite, and does --force replace it?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-apm-r4b/r4b.sh
```

## Outcome

Same setup as spike 5, but condition (a) required APM's own output to name the skipped path. APM 0.33.0 exited 0 and printed `[!] 1 file skipped -- local files exist, not managed by APM` on both a plain and a `-v` run, yet neither run named `.claude/skills/audit` (only a count). The lockfile omits the skipped skill from `deployed_files`. `--force` replaced SKILL.md with the package bytes and deleted notes.txt; the hand rule was overwritten without `--force`. Superseded by spike 5, which also tries `--dry-run` and accepts a path derived from the lockfile.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/r4b.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-apm-r4b/r4b.sh`, which the command used
