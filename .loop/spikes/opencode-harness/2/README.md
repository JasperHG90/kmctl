---
type: spike
title: Spike opencode-harness/2
description: can an OpenCode project plugin in .opencode/ add text to the system prompt at session start, and run a shell command without failing?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-17T21:49:37+00:00'
slug: opencode-harness
n: 2
outcome_written: true
---

# Spike opencode-harness/2

can an OpenCode project plugin in .opencode/ add text to the system prompt at session start, and run a shell command without failing?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/1/opencode-briefing-hook.sh /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/opencode-src
```

## Outcome

Exit 0: all 15 source checks held in OpenCode 9d97a5b. OpenCode loads `.ts`/`.js` files (or directories) from `.opencode/plugin/` or `.opencode/plugins/` (core/src/plugin/source-directory.ts:7,23). Each file needs a default export `{ id, setup }` (core/src/plugin/module.ts:79-89). Its `ctx.session.hook("context", e => ...)` gets a mutable `e.system: SystemPart[]` (`{type:"text", text}`) before every primary model request (plugin/src/promise/session.ts:28,140; core/src/session/model-request.ts:427), the way the built-in identity plugin adds a part (core/src/plugin/identity.ts:27).
This rules out "no hook can add text to context". The text goes in on every request, not once at session start. For a one-time message, the alternative is `ctx.event.subscribe()` on `session.created` plus `ctx.session.synthetic(...)` (core/src/plugin/plan.ts:78,84).
Plugins run in-process under Bun, so `node:child_process` can run `kmctl briefing`. OpenCode does not catch a rejected setup or hook (plugin/src/promise/adapter.ts:594,620), so the plugin itself must catch every error.
Settles risk 1. Limits: this was a source read, not a live OpenCode run, and main is the V2 plugin API (@opencode/plugin 2.0.32). A V1 `export const X = async () => ({...hooks})` module fails this loader's schema.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/opencode-briefing-hook.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/1/opencode-briefing-hook.sh`, which the command used
