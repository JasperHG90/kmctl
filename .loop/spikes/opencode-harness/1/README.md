---
type: spike
title: Spike opencode-harness/1
description: 'does OpenCode 9d97a5b load a .opencode/agents/NAME.md with description, mode: subagent and a tools name->bool mapping (no name key), and which keys, folder and tool names does its agent schema take?'
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-17T21:49:18+00:00'
slug: opencode-harness
n: 1
outcome_written: true
---

# Spike opencode-harness/1

does OpenCode 9d97a5b load a .opencode/agents/NAME.md with description, mode: subagent and a tools name->bool mapping (no name key), and which keys, folder and tool names does its agent schema take?

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/2/check_agent_schema.py /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/opencode-src
```

## Outcome

Static read of sst/opencode 9d97a5b (no code run): all 21 required facts held, so a `.opencode/agents/NAME.md` with `description`, `mode: subagent` and a `tools` name->bool mapping, without `name`, loads. Both `agent/` and `agents/` are globbed (core/src/config/plugin/agent.ts:22), and the name comes from the file path (:183).
Any key outside the native set (model, request, system, description, mode, hidden, color, steps, disabled, permissions, variant) sends the file through the V1 schema. That schema keeps unknown keys, accepts `name`, and turns `tools` (marked `@deprecated Use 'permission'`) into allow/deny rules. Unknown keys are not refused: they go into `options` and then into request.body sent to the provider (v1/config/migrate.ts:45), so `effort` must be dropped. `model: inherit` is ignored (migrate.ts:70). A named colour outside hex and the theme names fails decoding, which drops the agent silently (agent.ts:204) rather than stopping start-up.
Built-in tools: read, grep, glob, edit, write, patch, shell, skill, subagent, question, webfetch, websearch. There is no `list` or `bash`. V1 maps bash to shell, task to subagent, and write/patch to edit (migrate.ts:28-32). A tool with no rule defaults to `ask`, and the last matching rule wins.
This settles risk 2: the translator's output loads. Its table should drop `list`, prefer `permission` (or `"*": deny` first) over the deprecated `tools`, and never pass `effort` or a named `color` through. Limit: the check reads source text only; no `opencode` binary was run.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/check_agent_schema.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/2/check_agent_schema.py`, which the command used
