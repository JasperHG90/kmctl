---
type: spike
title: Spike antigravity-apm-audit/4
description: can kmctl's apm/apm.yml or the consumer's apm.yml (rename okf-bundle to bundle, re-declare bundle, --trust-transitive-mcp, okf-skills targets or skills subset) make APM 0.33.0 apm audit --ci pass config-consistency and drift for a claude+antigravity install after kmctl plugin patch?
tags:
- spike
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T15:03:21+00:00'
slug: antigravity-apm-audit
n: 4
outcome_written: true
---

# Spike antigravity-apm-audit/4

can kmctl's apm/apm.yml or the consumer's apm.yml (rename okf-bundle to bundle, re-declare bundle, --trust-transitive-mcp, okf-skills targets or skills subset) make APM 0.33.0 apm audit --ci pass config-consistency and drift for a claude+antigravity install after kmctl plugin patch?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-audit-r2/spike.sh
```

## Outcome

Exit 1: the risk is real for `config-consistency`, not for `drift`. Seven variants, each a claude+antigravity install of this checkout's `apm/` served from a file:// copy, then `kmctl plugin patch`, then `apm audit --ci --no-policy --no-fail-fast` (APM 0.33.0). The base case fails both checks, as issue #28 says.
`config-consistency` passes when kmctl's `apm/apm.yml` renames `okf-bundle` to `bundle`: only one server `bundle`, holding kmctl's launcher, in .mcp.json and .agents/mcp_config.json. It also passes with `apm install --trust-transitive-mcp` or with the consumer re-declaring okf's `bundle`, but those add okf's own server config next to `okf-bundle` (or in its place, when the package drops it).
`drift` on .agents/hooks.json still fails in every variant that keeps okf's skills under .agents/. No option keeps okf's Stop handler out at install: a `skills:` subset on okf-skills still deploys the hook. `targets: [claude]` on okf-skills clears drift, but it also drops okf's skills and okf-stop-check.sh from .agents/, and kmctl's Stop wrapper needs that script.
Settles risk 2: kmctl can clear `config-consistency` itself (rename the server), but not `drift`. Limits: one run; okf-skills came from GitHub at a8b96420; kmctl's other code that names `okf-bundle` (doctor, patch) was not checked against the rename.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-audit-r2/spike.sh`, which the command used
