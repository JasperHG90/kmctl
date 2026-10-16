---
type: spike
title: Spike apm-only-install/5
description: does apm install print a greppable skip line for a hand-made skill it will not overwrite, can kmctl find the skipped path, and does --force replace it?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:20:08+00:00'
slug: apm-only-install
n: 5
outcome_written: true
---

# Spike apm-only-install/5

does apm install print a greppable skip line for a hand-made skill it will not overwrite, can kmctl find the skipped path, and does --force replace it?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-apm-r4b/r4c.sh
```

## Outcome

The changed plan for risk 4 holds on APM 0.33.0 (exit 0). Over a hand-made `.claude/skills/audit/` a plain `apm install URL --target claude` exits 0 and prints the stable line `[!] 1 file skipped -- local files exist, not managed by APM` then `Use 'apm install --force' to overwrite`; grep for `skipped -- local files exist`. The `-v` run adds `[!] 1 file skipped (local files exist)` and repeats the line.
APM never names the skipped path: not in plain, `-v` or `--dry-run` output (`--dry-run` does not preview skips at all). kmctl can derive it: the package's `.apm/skills/audit/` is in `apm_modules/` but `.claude/skills/audit` is missing from `deployed_files` in `apm.lock.yaml`.
`apm install --force` exits 0, replaces SKILL.md with the package bytes and deletes the hand-made notes.txt (whole folder replaced). It prints a misleading `1 skill replaced by a different package (last installed wins)`.
The hand-written `.claude/rules/okf-bundle.md` is overwritten without `--force`, reported only as `[*] rewritten:` on `-v`. The real ~/.claude was untouched. Limit: one package with one skill; with several skipped files the line gives only a count.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/r4c.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-apm-r4b/r4c.sh`, which the command used
