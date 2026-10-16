---
type: spike
title: Spike kmctl-doctor/3
description: after apm 0.33.0 installs pinned okf-skills (Stop hook) for claude+antigravity and kmctl merges a SessionStart entry into .claude/settings.json, does apm.lock.yaml list hook or settings files, and do all listed sha256 still match?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:23:19+00:00'
slug: kmctl-doctor
n: 3
outcome_written: true
---

# Spike kmctl-doctor/3

after apm 0.33.0 installs pinned okf-skills (Stop hook) for claude+antigravity and kmctl merges a SessionStart entry into .claude/settings.json, does apm.lock.yaml list hook or settings files, and do all listed sha256 still match?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-p23/hooks_lock.sh
```

## Outcome

Answers review finding p2. `apm install` (0.33.0) of okf-skills at a8b96420 with `targets: [claude, antigravity]` wrote the Stop hook to `.claude/settings.json` and `.agents/hooks.json` (plus `.claude/apm-hooks.json`, `.agents/apm-hooks.json`, `.mcp.json`, `.agents/mcp_config.json`). The lock lists 40 deployed paths with 32 sha256 hashes.
The lock lists only the hook **scripts** (`.claude/hooks/okf-skills/hooks/okf-stop-check.sh`, `.agents/hooks/...`). It never lists `.claude/settings.json`, `.agents/hooks.json` or the `apm-hooks.json` files. The MCP server appears only as a `kind: uri` deployment, with no file.
After a kmctl-style SessionStart merge into `.claude/settings.json`, all 32 listed hashes still match the files on disk (0 mismatches). So the merge cannot make doctor's lock hash check report drift. It also means the lock cannot show whether the Stop hook entry in settings.json is still there; doctor must parse settings.json and hooks.json itself.
Settles risk 1 for the hash part. Limits: one package and one merge shape; network fetch from github.com.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/hooks_lock.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-p23/hooks_lock.sh`, which the command used
