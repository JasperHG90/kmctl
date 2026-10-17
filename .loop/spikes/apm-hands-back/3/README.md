---
type: spike
title: Spike apm-hands-back/3
description: over a kmctl-written install (SessionStart hook in settings.json, okf-bundle in .mcp.json), does APM 0.33.0 installing kmctl's package with the same hook and server keep the hook commands byte for byte, and does it duplicate or skip what kmctl wrote?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:52:35+00:00'
slug: apm-hands-back
n: 3
outcome_written: true
---

# Spike apm-hands-back/3

over a kmctl-written install (SessionStart hook in settings.json, okf-bundle in .mcp.json), does APM 0.33.0 installing kmctl's package with the same hook and server keep the hook commands byte for byte, and does it duplicate or skip what kmctl wrote?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate.sh
```

## Outcome

Exit 0 (an observation spike; the script prints and does not judge). With a consumer already holding kmctl-written pieces (kmctl's SessionStart group with no matcher in .claude/settings.json, okf-bundle and another server in .mcp.json), apm 0.33.0 installing a package that ships the same SessionStart hook (claude sub-package), the agy SessionStart and okf Stop wrapper (antigravity sub-package) and okf-bundle under dependencies.mcp: every hook command and the MCP launcher landed byte for byte (APM rewrote nothing); other keys and the other server stayed. Two migration facts: settings.json then held TWO kmctl SessionStart groups, kmctl's old one and APM's (APM's carries matcher '*' and is recorded in .claude/apm-hooks.json with _apm_source; kmctl's is not), so the old one must be removed by kmctl; and APM printed 'okf-bundle already configured, skipping' for .mcp.json yet recorded okf-bundle in the lock's mcp_servers and mcp_configs for claude and antigravity, so an identical entry needs no migration, while an entry with an older okf pin would stay stale until removed.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-migrate.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate.sh`, which the command used
