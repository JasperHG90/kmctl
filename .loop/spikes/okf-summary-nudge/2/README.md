---
type: spike
title: Spike okf-summary-nudge/2
description: does a Claude Code PostToolUse hook (matcher Write|Edit|MultiEdit|Bash) get cwd, tool_name and tool_input, and does its hookSpecificOutput.additionalContext reach the model after Write and Bash?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:49:03+00:00'
slug: okf-summary-nudge
n: 2
outcome_written: true
---

# Spike okf-summary-nudge/2

does a Claude Code PostToolUse hook (matcher Write|Edit|MultiEdit|Bash) get cwd, tool_name and tool_input, and does its hookSpecificOutput.additionalContext reach the model after Write and Bash?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge/risk1.sh
```

## Outcome

- Claude Code 2.1.302, `claude -p --model haiku`, PostToolUse hook with matcher `Write|Edit|MultiEdit|Bash` and `timeout: 10`: the hook fired after both Write and Bash, and its `hookSpecificOutput.additionalContext` reached the model: both final answers said "pineapple" (4 of 4 runs exited 0, 5 to 7 s each).
- Hook stdin held `cwd` (the repo root claude was started in), `tool_name` (`Write`/`Bash`), `tool_input` (`file_path`+`content`, or `command`), plus `tool_response`, `hook_event_name`, `session_id`, `transcript_path`; the hook's `$PWD` and `CLAUDE_PROJECT_DIR` were the repo root too.
- A hook that prints nothing, or `{}`, with exit 0 is harmless: the tool ran and the answer was normal.
- Limits: Edit and MultiEdit were not exercised (same matcher); claude was started at the repo root, not a subdirectory; hook timeout behaviour was not measured (10 s was simply set). Settles risk 1.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/risk1.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge/risk1.sh`, which the command used
