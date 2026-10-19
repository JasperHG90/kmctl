---
type: spike
title: Spike review-due-commit-order/1
description: 'does the commit-order rule for review due (verification commit = oldest commit holding the newest verified[].at; source changed by git diff V HEAD; edited after verification outside verified/stale_after) give the expected answers for issues #17 (squash, rebase, merge commit) and #18 and docs pages, and how much does the history walk add to the 0.56 s review due on kmctl?'
tags:
- spike
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:37:17+00:00'
slug: review-due-commit-order
n: 1
outcome_written: true
---

# Spike review-due-commit-order/1

does the commit-order rule for review due (verification commit = oldest commit holding the newest verified[].at; source changed by git diff V HEAD; edited after verification outside verified/stale_after) give the expected answers for issues #17 (squash, rebase, merge commit) and #18 and docs pages, and how much does the history walk add to the 0.56 s review due on kmctl?

The command exited 1:

```
uv run --frozen python /tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-review-due/commit_order.py
```

## Outcome

All 33 rule cases matched (same cases as run 2), so the rule picks the right verification commit after a squash, a rebase+ff and a merge commit.
Exit 1 came only from the timing check, which counted the per-source `git diff V HEAD` calls as added cost. They replace today's `git log -1` calls, so that check measured the wrong thing; run 2 fixes it.
Worst case, all 40 concepts and docs pages walking their whole history: one `git log` per file took 1.494 s, one batched `git log --name-only` plus one `git cat-file --batch` took 0.210 s; `review due` itself took 1.094 s on this busy machine.
Does not settle risk 1 on its own; see run 2.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/commit_order.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-review-due/commit_order.py`, which the command used
