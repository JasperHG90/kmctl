---
type: spike
title: Spike okf-summary/1
description: does a commit-order freshness rule (concepts changed after the last commit to .okf/summary.md, or uncommitted while the summary is not) flag the right concepts across same-commit, uncommitted, kmctl verify, log/index/handoff and ack edits, and run fast on kmctl?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T19:42:41+00:00'
slug: okf-summary
n: 1
outcome_written: true
---

# Spike okf-summary/1

does a commit-order freshness rule (concepts changed after the last commit to .okf/summary.md, or uncommitted while the summary is not) flag the right concepts across same-commit, uncommitted, kmctl verify, log/index/handoff and ack edits, and run fast on kmctl?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-sum1/freshness.py
```

## Outcome

All 10 scratch-repo cases pass: a decision committed after the summary is flagged by name; a decision in the same commit as the summary, or followed by a later summary commit, is not; uncommitted concept edits (tracked and untracked) are flagged until the summary is also edited uncommitted; an `ack` that writes `checked:` into the summary's front matter clears it; log.md, index.md and handoff edits never count.
A `kmctl verify` stamp (front-matter `verified:` plus log.md) committed after the summary flags that concept: an expected nudge rather than a miss, cleared by `ack`; a stamp written before the summary edit is covered.
Speed on kmctl itself (no summary yet, so the whole bundle counts): the full check takes 24-54 ms; `git diff --name-only ROOT..HEAD -- .okf` alone takes 2 ms.
Real history: 29 of the 40 concept-changing non-loop commits change more than one concept, and one commit (49439dd4) changed only the front matter of 2 decisions, so verify-style edits do occur and will nudge.
Limits: the uncommitted-summary branch clears committed concept changes too (the plan's "an edit to the summary clears it"); renames are read from the new path only; untracked files counted with --untracked-files=all.
Settles risk 1: the rule neither flags a same-session summary update nor misses verify edits.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/freshness.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-sum1/freshness.py`, which the command used
