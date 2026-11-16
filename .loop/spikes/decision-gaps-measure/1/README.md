---
type: spike
title: Spike decision-gaps-measure/1
description: Do hidden positives still name a decision after stripping ADR and decision sentences from subject, body and plan intent?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T11:47:23+00:00'
slug: decision-gaps-measure
n: 1
outcome_written: true
---

# Spike decision-gaps-measure/1

Do hidden positives still name a decision after stripping ADR and decision sentences from subject, body and plan intent?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/gaps/scripts/leak_check.py . /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/gaps/results/units.jsonl
```

## Outcome

Settled for the words, not for the shape: after stripping, none of the 31 hidden positives (27 with a plan intent) still names an ADR, a decision or a recorded choice, so the judge cannot read the answer off the text. What stays is the plan's description of the change itself, including any rejected option it names; a real unrecorded decision's plan carries the same, so that is signal, not leak. The README reports the judge's recall with that caveat, and the false-alarm rate on negatives bounds how much a generous judge inflates it.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
