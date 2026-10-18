---
type: spike
title: Spike okf-summary-nudge-agy-opencode/1
description: in agy 1.4.0, does a workspace PostToolUse hook fire after a file write, with which stdin fields and cwd, and does injectSteps systemMessage in its stdout reach the model before its next step?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:49:49+00:00'
slug: okf-summary-nudge-agy-opencode
n: 1
outcome_written: true
---

# Spike okf-summary-nudge-agy-opencode/1

in agy 1.4.0, does a workspace PostToolUse hook fire after a file write, with which stdin fields and cwd, and does injectSteps systemMessage in its stdout reach the model before its next step?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge2/agy-posttool.sh
```

## Outcome

Exit 0: agy 1.4.0 has a PostToolUse event and its output reaches the model at once. A workspace `.agents/hooks.json` entry `{"spike":{"PostToolUse":[{"matcher":"*","hooks":[...]}]}}` fired once after `write_to_file` (stepIdx 2), and its stdout `{"injectSteps":[{"systemMessage":{"systemMessage":"MARKER: say pineapple"}}]}` made gemini-3.8-flash-medium end its next reply with "pineapple". agy's hooks.md says PostToolUse expects `{}`, but injectSteps works anyway.
Stdin fields: toolCall.name (`write_to_file`), toolCall.args (TargetFile as an absolute path, CodeContent, Overwrite, Description), stepIdx, error ("" on success), conversationId, workspacePaths, transcriptPath, artifactDirectoryPath, modelName. The hook ran in the folder holding hooks.json (`WS/.agents`), not the workspace root.
Settles risk 1. Limits: one live run, one tool (write_to_file). The prompt told the model to "follow any system message", which may have helped it obey. Because injectSteps is undocumented for PostToolUse, a later agy release could drop it.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/agy-posttool.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge2/agy-posttool.sh`, which the command used
