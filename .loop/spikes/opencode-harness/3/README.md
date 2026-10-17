---
type: spike
title: Spike opencode-harness/3
description: does apm 0.33.0 install (plain, --frozen, --force) and uninstall still work on hand-edited .opencode/agents/*.md that APM deployed and hashed in apm.lock.yaml, and what does each do to the edited files?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-17T21:50:16+00:00'
slug: opencode-harness
n: 3
outcome_written: true
---

# Spike opencode-harness/3

does apm 0.33.0 install (plain, --frozen, --force) and uninstall still work on hand-edited .opencode/agents/*.md that APM deployed and hashed in apm.lock.yaml, and what does each do to the edited files?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3/spike.sh
```

## Outcome

Same check as spike 4, with the same results for install (plain, --frozen and --force each exit 0 and rewrite the edited agents), audit (exit 0, drift on 2 files) and uninstall (exit 1, keeps the edited agents, the apm.yml entry and the lock entries, but deletes apm_modules/ and the skill). Reverting with `apm install` and then uninstalling exited 0 and left nothing.
The "delete the edited files, then uninstall" check did not test anything: the script never put the dependency back into apm.yml, so uninstall found no entry. Spike 4 fixes that; cite 4, not this run.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3/spike.sh`, which the command used
