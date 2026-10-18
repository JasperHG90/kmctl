---
type: spike
title: Spike starter-reviewer-gitignore/3
description: with the adversarial-reviewer.agent.md dependency (pinned 41f49502), do just bootstrap, the generated hooks, kmctl check and doctor pass for [claude] and [claude, antigravity, opencode], and where does the agent land?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:28:14+00:00'
slug: starter-reviewer-gitignore
n: 3
outcome_written: true
---

# Spike starter-reviewer-gitignore/3

with the adversarial-reviewer.agent.md dependency (pinned 41f49502), do just bootstrap, the generated hooks, kmctl check and doctor pass for [claude] and [claude, antigravity, opencode], and where does the agent land?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-reviewer3/spike.py
```

## Outcome

Exit 0. With `adversarial-reviewer.agent.md#41f49502` appended, `just bootstrap` exits 0 for [claude] and for [claude, antigravity, opencode]. The agent lands at `.claude/agents/adversarial-reviewer.md` in both, plus `.opencode/agents/adversarial-reviewer.md` in the three-harness set. Nothing lands for antigravity.
After `git add -A`, `uvx prek@0.5.5 run --all-files` exits 0 (all hooks pass), `kmctl check` exits 0, and `kmctl doctor --json` fails only dep.claude (and dep.agy, dep.opencode for three harnesses). `kmctl plugin patch` printed no warning about the agent.
Rules out patch, doctor or hooks failing on the `.opencode/` copy. Settles risk 2.
Limit: APM itself warns during install that the OpenCode copy "has tools as str" and "has color='red'; OpenCode requires a hex value ... OpenCode will reject this agent". The opencode binary is not installed here, so whether OpenCode loads the agent at runtime is not tested; that is a separate risk.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-reviewer3/spike.py`, which the command used
