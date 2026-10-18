---
type: spike
title: Spike okf-summary-nudge/3
description: does APM 0.33.0 deploy a PostToolUse entry with matcher Write|Edit|MultiEdit|Bash from a package's hooks.json into .claude/settings.json, once across reinstalls, recorded, and removed on uninstall?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:50:08+00:00'
slug: okf-summary-nudge
n: 3
outcome_written: true
---

# Spike okf-summary-nudge/3

does APM 0.33.0 deploy a PostToolUse entry with matcher Write|Edit|MultiEdit|Bash from a package's hooks.json into .claude/settings.json, once across reinstalls, recorded, and removed on uninstall?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge/risk2.sh
```

## Outcome

- APM 0.33.0 (`apm install --target claude`, local path dependency `./pkg` copied from apm/claude with a PostToolUse entry added to `.apm/hooks/hooks.json`): `.claude/settings.json` got the PostToolUse entry with matcher `Write|Edit|MultiEdit|Bash`, description, command and `timeout: 10` byte for byte, next to the SessionStart one.
- A second `apm install` left exactly 1 PostToolUse and 1 SessionStart entry.
- apm.lock.yaml records the package (kmctl-claude 0.8.0) but names no hook and not settings.json, for SessionStart too; APM tracks hooks in `.claude/apm-hooks.json`, which held the PostToolUse entry with `_apm_source`. `apm uninstall ./pkg` cleaned the hooks and left settings.json `{}`.
- Limit: a local path install, not git; spike apm-hands-back/1 shows git installs use the same hook integrator. Settles risk 2; any plan step that expects the hook in apm.lock.yaml should look in .claude/apm-hooks.json instead.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/risk2.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge/risk2.sh`, which the command used
