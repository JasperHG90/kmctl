---
type: spike
title: Spike kmctl-doctor/2
description: after apm 0.33.0 installs pinned okf-skills (Stop hook) for claude+antigravity and kmctl merges a SessionStart entry into .claude/settings.json, does apm.lock.yaml list hook or settings files, and do all listed sha256 still match?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:23:19+00:00'
slug: kmctl-doctor
n: 2
outcome_written: true
---

# Spike kmctl-doctor/2

after apm 0.33.0 installs pinned okf-skills (Stop hook) for claude+antigravity and kmctl merges a SessionStart entry into .claude/settings.json, does apm.lock.yaml list hook or settings files, and do all listed sha256 still match?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-p23/hooks_lock.sh
```

## Outcome

Answers review finding p2. Discarded run: the check's regex also read the package-level `content_hash:` line as a file path and reported it as a mismatch (exit 1). The install and lock contents are valid, but the verdict is wrong. spike:kmctl-doctor/3 reruns it with the parser fixed. Does not settle risk 1.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/hooks_lock.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-p23/hooks_lock.sh`, which the command used
