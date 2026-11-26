---
type: spike
title: Spike adr-0057-pr-audit/2
description: can a loop/SLUG worktree cut from main merge PR 71 branch adr/audit-pull-requests past the git backstop so a push fast-forwards it, and can ticket done close without ticket land?
tags:
- spike
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T12:53:26+00:00'
slug: adr-0057-pr-audit
n: 2
outcome_written: true
---

# Spike adr-0057-pr-audit/2

can a loop/SLUG worktree cut from main merge PR 71 branch adr/audit-pull-requests past the git backstop so a push fast-forwards it, and can ticket done close without ticket land?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-r1/carry_pr71.sh
```

## Outcome

PR 71's head (c9985ad5) is 2 commits ahead of and 13 behind main, so the worktree must merge it, not fast-forward. `git merge-tree` merges main and PR 71 with no conflict, the merge contains PR 71's head (pushing it is a fast-forward), and PR 71 changes no `.loop/` path. In a throwaway clone with the real backstop hooks, creating `loop/adr-0057-pr-audit` from main and `git merge --no-ff --no-commit` of PR 71 both passed, and the commit-time `_merge_refusal` on MERGE_HEAD returned None.
From loopctl 2.4.0's source: `advance building` cuts `loop/SLUG` from `integration_branch` (or reuses an existing `loop/SLUG`). Plain `ticket done` takes the newest `Loop-Ticket` commit on `loop/SLUG` or main, so it does not need the commit on main and never calls land. `land` runs only after done, and once PR 71 is merged it only cleans up.
Settles risk 1. Limit: every commit in a ticket worktree needs a green stamp and passing verdicts, so the merge cannot be committed alone. Merge with `--no-commit`, make the ADR edits, and commit it all as the one `Loop-Ticket` commit (a merge commit). Do not run `ticket land` before PR 71 merges, because land would merge the branch into main. The done check was read from source, not run on a real ticket.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/carry_pr71.sh`: a copy of `/tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-r1/carry_pr71.sh`, which the command used
