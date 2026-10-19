---
type: spike
title: Spike review-due-commit-order/1
description: 'does the commit-order rule for review due (verification commit = oldest commit holding the newest verified[].at; source changed by git diff V HEAD; edited after verification outside verified/stale_after) give the expected answers for issues #17 (squash, rebase, merge commit) and #18 and docs pages, and how much does the history walk add to the 0.56 s review due on kmctl?'
tags:
- spike
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:35:35+00:00'
slug: review-due-commit-order
n: 1
outcome_written: false
---

# Spike review-due-commit-order/1

does the commit-order rule for review due (verification commit = oldest commit holding the newest verified[].at; source changed by git diff V HEAD; edited after verification outside verified/stale_after) give the expected answers for issues #17 (squash, rebase, merge commit) and #18 and docs pages, and how much does the history walk add to the 0.56 s review due on kmctl?

The command exited 1:

```
uv run --frozen python /tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-review-due/commit_order.py
```

## Outcome

Not written yet: `loopctl plan spike-note review-due-commit-order 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/commit_order.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-review-due/commit_order.py`, which the command used
