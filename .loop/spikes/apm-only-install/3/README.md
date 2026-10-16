---
type: spike
title: Spike apm-only-install/3
description: does apm install --target claude overwrite, skip, warn or fail on a .claude/rules/okf-bundle.md and .claude/skills/audit/ it did not write?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:17:34+00:00'
slug: apm-only-install
n: 3
outcome_written: true
---

# Spike apm-only-install/3

does apm install --target claude overwrite, skip, warn or fail on a .claude/rules/okf-bundle.md and .claude/skills/audit/ it did not write?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spikeuwRa/r4.full.sh
```

## Outcome

A project install with `apm install URL --target claude` (APM 0.33.0) exited 0 over a hand-written `.claude/rules/okf-bundle.md` and a hand-made `.claude/skills/audit/` (SKILL.md plus notes.txt). It treated the two differently:
- The rule was overwritten with the package text, reported only as `[*] rewritten: .claude/rules/okf-bundle.md`.
- The skill folder was left untouched: the old SKILL.md stayed and notes.txt survived. APM warned `[!] 1 file skipped -- local files exist, not managed by APM` and `Use 'apm install --force' to overwrite`.
The spike exits 1 because the skill was not replaced. Refusing is ruled out, and so is skipping silently. Risk 4 is real for skill folders: a repository with an old `audit` skill keeps the stale copy unless the install passes `--force`. This run did not test `--force`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/r4.full.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spikeuwRa/r4.full.sh`, which the command used
