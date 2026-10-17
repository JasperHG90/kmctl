---
type: spike
title: Spike antigravity-okf-stop-hook/3
description: in agy 1.4.0, does the first Stop of a second turn in the same conversation (agy -c) carry executionNum 0 again?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:36:49+00:00'
slug: antigravity-okf-stop-hook
n: 3
outcome_written: true
---

# Spike antigravity-okf-stop-hook/3

in agy 1.4.0, does the first Stop of a second turn in the same conversation (agy -c) carry executionNum 0 again?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-stop2.sh
```

## Outcome

Exit 0: executionNum counts within one turn, not across a conversation. In one conversation (turn 1 with agy -p, turn 2 with agy -c -p, same conversationId on all four Stop calls), the stops carried executionNum 0, 1 in turn 1 and 0, 1 again in turn 2; the hook continued once per turn and each turn then ended. So a guard on executionNum 0 means the first stop of each turn.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-stop2.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-stop2.sh`, which the command used
