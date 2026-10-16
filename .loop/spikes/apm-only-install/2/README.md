---
type: spike
title: Spike apm-only-install/2
description: does apm install -g of a package with no git parent work for --target claude, and where do the files land (does it honour CLAUDE_CONFIG_DIR)?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:17:18+00:00'
slug: apm-only-install
n: 2
outcome_written: true
---

# Spike apm-only-install/2

does apm install -g of a package with no git parent work for --target claude, and where do the files land (does it honour CLAUDE_CONFIG_DIR)?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spikeuwRa/r3.full.sh
```

## Outcome

`apm install -g URL --target claude --allow-insecure` (APM 0.33.0) took a package with no `git: parent` and exited 0. It kept its state in `$HOME/.apm/` (apm.yml, lock, apm_modules) and wrote the skill and agent byte for byte to `$CLAUDE_CONFIG_DIR/skills/audit/SKILL.md` and `$CLAUDE_CONFIG_DIR/agents/x.md`, plus the rule to `$CLAUDE_CONFIG_DIR/rules/okf-bundle.md` with `applyTo` turned into a `paths:` list. Those are the user-level folders Claude Code reads.
APM -g honours CLAUDE_CONFIG_DIR: an earlier unrecorded run with HOME pointed at scratch but CLAUDE_CONFIG_DIR=/home/vscode/.claude wrote into the real /home/vscode/.claude. This run set both to scratch and checked that nothing leaked into the real directory.
Limit: here CLAUDE_CONFIG_DIR was `$HOME/.claude`, so this run alone cannot tell the two variables apart. The refusal and wrong-place outcomes are ruled out, which settles risk 3: `--scope user` stays.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/r3.full.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spikeuwRa/r3.full.sh`, which the command used
