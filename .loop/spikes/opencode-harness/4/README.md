---
type: spike
title: Spike opencode-harness/4
description: does apm 0.33.0 install (plain, --frozen, --force) and uninstall still work on hand-edited .opencode/agents/*.md that APM deployed and hashed in apm.lock.yaml, and does deleting or reverting them first let uninstall finish?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-17T21:50:15+00:00'
slug: opencode-harness
n: 4
outcome_written: true
---

# Spike opencode-harness/4

does apm 0.33.0 install (plain, --frozen, --force) and uninstall still work on hand-edited .opencode/agents/*.md that APM deployed and hashed in apm.lock.yaml, and does deleting or reverting them first let uninstall finish?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3/spike.sh
```

## Outcome

With apm 0.33.0, a git-served package (subfolder `apm`, tag v0.1.0, two Claude-format agents and one skill) and `targets: [opencode]`, both deployed `.opencode/agents/*.md` were edited as patch would (tools string to a mapping, plus a marker line). Plain `apm install`, `--frozen` and `--force` each exited 0 and silently rewrote both edited agents back to APM's bytes (lock hashes unchanged); none skipped or refused, so `--force` changes nothing here. `apm audit` exits 0 but reports "Drift detected: 2 file(s)".
`apm uninstall` exits 1: "Retained user-edited file ... resolve it and retry", leaves both edited agents, apm.yml's entry and every lock entry, yet still deletes apm_modules/ and the skill's 2 files, so it fails half-done.
Both ways out work: a plain `apm install` first (reverts the edits) then uninstall, or deleting the edited agent files first then uninstall; each exits 0 and leaves no agent file, an empty `apm: []` and no apm.lock.yaml.
Risk 3 is real: patch must re-run after every `apm install`, and remove must delete or revert the patched agents before `apm uninstall`. Also seen: APM itself warns "OpenCode agent ... has tools as str; OpenCode will reject this agent at load time" (bears on risk 2). Limits: one run, a small package rather than kmctl's, project scope only.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3/spike.sh`, which the command used
