---
type: spike
title: Spike release-notes-hermes-reviewer-f2/1
description: how many real Hermes rewrites put a non-bullet line under What changed, which the checks never look at?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T04:47:49+00:00'
slug: release-notes-hermes-reviewer-f2
n: 1
outcome_written: true
---

# Spike release-notes-hermes-reviewer-f2/1

how many real Hermes rewrites put a non-bullet line under What changed, which the checks never look at?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/f2spike/count_stray.py .loop/spikes/release-notes-hermes/1/stdout.txt
```

## Outcome

## Outcome

0 of 16 rewrites in spike:release-notes-hermes/1 (the 15 Hermes rewrites of five real drafts, v0.9.0 to v0.12.1, and one more record in that output) put a line under What changed that is neither a bullet nor an indented continuation of one. On benign drafts the new check would not have fired, so it does not change which rewrites are kept today. What it guards is the case ADR 0035 names: a crafted commit subject in the draft steering the reply into adding unreferenced prose, which every current check passes. Benign history cannot show that rate; the cost is a few lines and a fall back to the draft, which is always safe.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/count_stray.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/f2spike/count_stray.py`, which the command used
