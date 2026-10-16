---
type: spike
title: Spike kmctl-doctor/1
description: does APM 0.33.0 install --target claude,antigravity record the targets in the consumer apm.yml or apm.lock.yaml, and does the lock list deployed .agents/ paths with sha256 like .claude/
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T19:46:59+00:00'
slug: kmctl-doctor
n: 1
outcome_written: true
---

# Spike kmctl-doctor/1

does APM 0.33.0 install --target claude,antigravity record the targets in the consumer apm.yml or apm.lock.yaml, and does the lock list deployed .agents/ paths with sha256 like .claude/

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-r1/targets.sh
```

## Outcome

APM 0.33.0 `install ../pkg --target claude,antigravity` exited 0 in both cases and deployed rules and skills to `.claude/` and `.agents/`.
- Fresh repo, no apm.yml: APM creates apm.yml and writes `targets: [antigravity, claude]` into it ("persisted to apm.yml").
- Existing apm.yml without `targets:`: APM adds the dependency but does **not** add `targets:`. The flag is recorded only in the lock.
- In both cases apm.lock.yaml lists `.agents/` paths exactly as it lists `.claude/` ones: `deployed_files`, `deployed_file_hashes` (sha256), and `deployments[]` entries with `target: antigravity` / `target: claude`.
Settles risk 1: targets can be recovered from apm.yml `targets:` or from the lock's `deployments[].target`. One gap remains: for a repo that already had an apm.yml, deleting the lock removes the only record of the targets. Limits: one local package with a skill and an instruction; no hook was deployed.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/targets.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-doctor-r1/targets.sh`, which the command used
