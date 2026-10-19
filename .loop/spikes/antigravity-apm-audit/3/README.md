---
type: spike
title: Spike antigravity-apm-audit/3
description: does apm audit --ci (APM 0.33.0) fail drift on .agents/hooks.json and config-consistency on bundle after apm install --target antigravity and kmctl plugin patch, pass for claude alone, and what does --no-drift leave?
tags:
- spike
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:35:43+00:00'
slug: antigravity-apm-audit
n: 3
outcome_written: true
---

# Spike antigravity-apm-audit/3

does apm audit --ci (APM 0.33.0) fail drift on .agents/hooks.json and config-consistency on bundle after apm install --target antigravity and kmctl plugin patch, pass for claude alone, and what does --no-drift leave?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-audit-r1/audit.sh
```

## Outcome

APM 0.33.0, kmctl 0.10.0 at 9f735466 served by file:// insteadOf, one scratch project per target. For `--target antigravity`, `apm audit --ci` after `kmctl plugin patch` failed 2 of 8 checks: `drift` ("modified: .agents/hooks.json") and `config-consistency` ("bundle: in manifest but not in lockfile"). Before the patch, drift passed and only config-consistency failed, so the patch's Stop-handler removal alone causes the drift.
The issue is wrong about one thing: `--target claude` does not pass. It fails `config-consistency` on `bundle` the same way, both before and after patch, while drift passes. So the bundle failure comes from okf's transitive server for every target, not just Antigravity. `--no-drift` leaves exit 1 for both targets, with config-consistency as the only failure.
At install, APM warns "Transitive package 'okf' declares self-defined MCP server 'bundle' (registry: false). Re-declare it in your apm.yml or use --trust-transitive-mcp", which is a lead for risk 2.
Risk 1 holds: no audit flag combination passes for either target. Limits: one run per target, project scope only, the policy check skipped (no git remote), okf-skills fetched from real GitHub. The exact output is in stdout.txt.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/audit.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-audit-r1/audit.sh`, which the command used
