---
type: spike
title: Spike opencode-harness/7
description: with the changed plan, does re-patching after every apm install and --frozen give identical bytes, and does deleting the translated agents let apm uninstall finish clean?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T04:14:19+00:00'
slug: opencode-harness
n: 7
outcome_written: true
---

# Spike opencode-harness/7

with the changed plan, does re-patching after every apm install and --frozen give identical bytes, and does deleting the translated agents let apm uninstall finish clean?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3b/spike.sh
```

## Outcome

With apm 0.33.0 and spike 4's fixture (git-served package, subfolder `apm`, tag v0.1.0, two Claude-format agents, one skill, `targets: [opencode]`), every assertion of the changed flow passed. Step 1: install exits 0, a deterministic patch rewrites both agents to hash H, and re-patching its own output changes nothing. Step 2: a plain `apm install` exits 0 and reverts both agents to APM's raw bytes; re-patching gives H again, the whole file tree under `.opencode/` and `.agents/` matches step 1, and `apm.lock.yaml` is unchanged. Step 3: `apm install --frozen` behaves the same way, and re-patching gives H.
Step 4: deleting only the translated agents, then `apm uninstall`, exits 0 ("Cleaned 2 stale files"). It leaves no `.opencode/agents/*.md`, no skill files, no apm_modules/, no apm.lock.yaml, and apm.yml has `apm: []`.
This settles risk 3 as rewritten: re-patching after every install is stable, and undo-then-uninstall finishes clean. It does not test doctor's detection of a bare install. Limits: one run, a small package rather than kmctl's, project scope only, and the fixture writes no opencode.json, so that file is checked only for being absent. The two stderr lines come from hashing an empty agents folder after undo and do not matter.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3b/spike.sh`, which the command used
