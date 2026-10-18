---
type: spike
title: Spike starter-reviewer-gitignore/1
description: 'does APM 0.33.0 accept a #sha-pinned single-file agent dependency (jasperhg90/skills adversarial-reviewer.md) in a starter project, with just bootstrap, kmctl check and doctor passing for claude, opencode, antigravity and all three?'
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:18:30+00:00'
slug: starter-reviewer-gitignore
n: 1
outcome_written: true
---

# Spike starter-reviewer-gitignore/1

does APM 0.33.0 accept a #sha-pinned single-file agent dependency (jasperhg90/skills adversarial-reviewer.md) in a starter project, with just bootstrap, kmctl check and doctor passing for claude, opencode, antigravity and all three?

The command exited 1:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-reviewer/spike.py
```

## Outcome

For all four harness sets ([claude], [opencode], [antigravity], [claude, antigravity, opencode]), `just bootstrap` exits 1 at `apm install`. APM 0.33.0 rejects the dependency while it parses apm.yml: "Invalid virtual package path 'agents/adversarial-reviewer.md'. Individual files must end with one of: .prompt.md, .instructions.md, .agent.md."
APM therefore installs nothing, and `kmctl plugin patch` and `kmctl init` never run. The doctor failures beyond dep.* (claude.*, opencode.*, antigravity.*, init.*) all follow from that. No adversarial-reviewer file lands anywhere.
The cause is the upstream file name (`.md`, not `.agent.md`), not the harness or the pin. Spike 2 shows the unpinned form fails the same way.
Settles risk 1: the risk is real. On APM 0.33.0 no harness set can get this agent from apm.yml as the file is named at 09b7a0a8.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-reviewer/spike.py`, which the command used
