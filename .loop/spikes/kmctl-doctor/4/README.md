---
type: spike
title: Spike kmctl-doctor/4
description: with a scratch HOME and warm uv cache, do uv tool run --offline apm-cli==0.33.0 apm --version and claude plugin list --json run without network connections, and does claude plugin list leave HOME unchanged?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:24:28+00:00'
slug: kmctl-doctor
n: 4
outcome_written: true
---

# Spike kmctl-doctor/4

with a scratch HOME and warm uv cache, do uv tool run --offline apm-cli==0.33.0 apm --version and claude plugin list --json run without network connections, and does claude plugin list leave HOME unchanged?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-p23/offline.sh
```

## Outcome

Answers review finding p3. `unshare -rn` is not allowed in this container, so the run watched `connect()` with strace instead of blocking the network.
After warming the cache, `uv tool run --offline --from apm-cli==0.33.0 apm --version` exited 0 and printed 0.33.0. It made 0 AF_INET/AF_INET6 connects and changed no file under the scratch HOME, so this half holds.
`claude plugin list --json` (2.1.301) exited 0 and printed `[]`, but it made 4 inet connects (2 DNS on :53, 2 to 160.79.104.10:443). It also wrote `$CLAUDE_CONFIG_DIR/.claude.json` (firstStartTime, machineID, userID, migration flags) plus a `backups/.claude.json.backup.*` file.
So doctor cannot treat `claude plugin list` as a read-only, offline probe. The risk is real for that half and is not settled.
Limits: a fresh, empty CLAUDE_CONFIG_DIR, so some writes may be first-run only. Not tested with CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC. The real ~/.claude/agents, rules and skills/audit stayed absent.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/offline.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-p23/offline.sh`, which the command used
