---
type: spike
title: Spike review-due-commit-order/2
description: 'does the commit-order rule for review due (verification commit = oldest commit holding the newest verified[].at; source changed by git diff V HEAD; edited after verification outside verified/stale_after) give the expected answers for issues #17 (squash, rebase, merge commit) and #18 and docs pages, and how much does the history walk add to the 0.56 s review due on kmctl?'
tags:
- spike
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:37:20+00:00'
slug: review-due-commit-order
n: 2
outcome_written: true
---

# Spike review-due-commit-order/2

does the commit-order rule for review due (verification commit = oldest commit holding the newest verified[].at; source changed by git diff V HEAD; edited after verification outside verified/stale_after) give the expected answers for issues #17 (squash, rebase, merge commit) and #18 and docs pages, and how much does the history walk add to the 0.56 s review due on kmctl?

The command exited 0:

```
uv run --frozen python /tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-review-due/commit_order.py
```

## Outcome

The rule passed all 33 cases in scratch repos built with this checkout's kmctl. Issue #17's steps (main moved on first) landed by squash, rebase+ff and merge commit: not due after landing; `source changed` after a later source commit; `edited after verification` after a body or description edit; nothing after a re-verify, with or without `--stale-after`, or after a source change followed by a re-verify. Issue #18: an appended line gives `edited after verification`. A verify entry never committed gives nothing. A docs page follows the same rules, and one without `verified` uses its own last commit.
Speed on kmctl (2900 commits), worst case with all 40 concepts and docs pages walking their whole history: one `git log` per file takes 1.765 s, so that design is ruled out. One batched `git log --name-only` plus one `git cat-file --batch` takes 0.359 s. The per-source `git diff --quiet` calls take 0.270 s against 0.683 s for the `git log -1` calls they replace, so the net cost is -0.054 s. Today no file is verified, so the real walk costs 0 s.
Limits: the machine was busy (`review due` ran in 1.257 s, not 0.56 s), so read the times relative to each other. The batched log saw 308 versions where the per-file logs saw 341, because merges and renames drop out of a union pathspec. The rule cases used per-file `git log`, so the batched walk's choice of V is not tested here.
Settles risk 1, provided the walk is batched: the right commit in all three landing styles, and no measurable slowdown.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/commit_order.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-review-due/commit_order.py`, which the command used
