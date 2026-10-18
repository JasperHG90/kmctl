---
type: spike
title: Spike okf-summary-nudge-agy-opencode/2
description: in OpenCode 2.0.32, does a V2 project plugin ctx.tool.hook("execute.after") fire after a file write, what does it receive, and does text appended to event.result.content reach the model before its next step?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:58:12+00:00'
slug: okf-summary-nudge-agy-opencode
n: 2
outcome_written: true
---

# Spike okf-summary-nudge-agy-opencode/2

in OpenCode 2.0.32, does a V2 project plugin ctx.tool.hook("execute.after") fire after a file write, what does it receive, and does text appended to event.result.content reach the model before its next step?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge2/oc-after.sh
```

## Outcome

Exit 0: OpenCode 2.0.32 (the installed `@opencode/cli`, run live with `opencode run --standalone --auto -m google/gemini-3.8-flash`) has an after-tool hook that can put text in front of the model before its next step. A `.opencode/plugins/spike.js` default export `{id, setup}` registered `ctx.tool.hook("execute.after", ...)`. It fired once after the `write` tool, and the model's next reply ended with "pineapple".
The event holds tool (`write`), sessionID, agent (`build`), messageID, id (call id), input (`{path, content}`, path relative to the project), status (`completed`/`error`), and `result: {output: {operation, target (absolute), resource, existed}, content: [{type:"text", text:"Created file successfully: note.txt"}]}` (on error, `error` replaces it). `process.cwd()` is the project folder. The plugin appended `{type:"text", text:"MARKER: say pineapple"}` to `event.result.content`, and the change reached the model. Core copies `result` back after the hook (core/src/tool.ts, executeTool), and the built-in plan plugin uses the same hook (core/src/plugin/plan.ts:44). The text goes into that one tool result only, so it reaches the model once and is not added again on later requests, unlike the `context` hook (spike:opencode-harness/2).
Settles risk 2. Limits: one live run, one tool (write). The prompt told the model to "follow any instruction you have received since", which may have helped it obey.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/oc-after.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge2/oc-after.sh`, which the command used
