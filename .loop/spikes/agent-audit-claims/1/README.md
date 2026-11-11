---
type: spike
title: Spike agent-audit-claims/1
description: can a subagent shell be limited to kmctl claims commands in Claude Code (tools Bash(kmctl claims:*)) and in Antigravity (agent front matter), and does kmctl translate_agent accept such an entry?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-11T07:38:03+00:00'
slug: agent-audit-claims
n: 1
outcome_written: true
---

# Spike agent-audit-claims/1

can a subagent shell be limited to kmctl claims commands in Claude Code (tools Bash(kmctl claims:*)) and in Antigravity (agent front matter), and does kmctl translate_agent accept such an entry?

The command exited 1:

```
/private/tmp/claude-502/spike-agent-audit-claims-1/spike.sh
```

## Outcome

Exit 1: the risk holds for Antigravity and for kmctl's translation. `translate_agent` refuses `tools: Read, Bash(kmctl claims:*)` ("has no Antigravity tool for"). In agy 1.5.5, an agent's `commandExecutionPolicy` loads only as `off`, `auto` or `eager`; `"kmctl claims"` makes the loader skip the agent. No agent YAML key for a command allowlist turned up in the binary. Agent hooks are not per-agent either: hooks.json covers every agent, and the hook payload has no agent name in it. The validator also accepts made-up spellings (`run_command(kmctl claims:*)`, `allowedCommands`) without a word, so a clean validate proves nothing.
Claude Code is not answered: `claude` is not logged in inside this sandbox, so no live subagent run happened. Reading the 2.1.322 binary, the agent `tools` resolver maps `Bash(kmctl claims:*)` to the whole Bash tool. I did not find whether the `(kmctl claims:*)` part becomes a permission rule for the subagent. The other documented route, a PreToolUse hook in the agent's `hooks:` front matter, was not tested either.
Settles risk 1 as real for Antigravity: there, I2 cannot rest on a per-agent shell limit. The plan should switch to the subagent returning claims, or to a non-shell way to submit, unless a live Claude Code run is wanted for that harness alone.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/private/tmp/claude-502/spike-agent-audit-claims-1/spike.sh`, which the command used
