---
type: spike
title: Spike pr-reread-only/1
description: does widening the PR scope from stable decisions to every .okf/ and docs/ page with sources add pages, over the last 15 merged PRs?
tags:
- spike
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-27T10:32:21+00:00'
slug: pr-reread-only
n: 1
outcome_written: true
---

# Spike pr-reread-only/1

does widening the PR scope from stable decisions to every .okf/ and docs/ page with sources add pages, over the last 15 merged PRs?

The command exited 0:

```
python /tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/proto/scope.py origin/main 15
```

## Outcome

Widening adds pages. Over the last 15 merged pull requests from origin/main (91b5ab5a back to 6de2f9f1), the stable-decisions scope found 64 pages and the wide scope 72; the 8 more are docs pages, 2 each in #72, #74, #77 and its loop merge. Architecture and practices pages name no sources today, so they add none. The risk does not hold; the script is the prototype pr-reread-scope.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/scope.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/proto/scope.py`, which the command used
