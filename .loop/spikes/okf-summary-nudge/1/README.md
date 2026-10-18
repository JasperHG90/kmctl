---
type: spike
title: Spike okf-summary-nudge/1
description: does a Claude Code PostToolUse hook (matcher Write|Edit|MultiEdit|Bash) get cwd, tool_name and tool_input, and does its hookSpecificOutput.additionalContext reach the model after Write and Bash?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:48:26+00:00'
slug: okf-summary-nudge
n: 1
outcome_written: true
---

# Spike okf-summary-nudge/1

does a Claude Code PostToolUse hook (matcher Write|Edit|MultiEdit|Bash) get cwd, tool_name and tool_input, and does its hookSpecificOutput.additionalContext reach the model after Write and Bash?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge/risk1.sh
```

## Outcome

- Broken command, not evidence: `--allowedTools "Write Edit Bash"` is variadic and swallowed the prompt, so every `claude -p` run failed with "Input must be provided".
- Shows nothing about the risk; spike 2 reruns with `--allowedTools=Write,Edit,Bash`. Does not settle risk 1.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/risk1.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge/risk1.sh`, which the command used
