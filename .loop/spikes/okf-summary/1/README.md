---
type: spike
title: Spike okf-summary/1
description: does a commit-order freshness rule (concepts changed after the last commit to .okf/summary.md, or uncommitted while the summary is not) flag the right concepts across same-commit, uncommitted, kmctl verify, log/index/handoff and ack edits, and run fast on kmctl?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T19:42:31+00:00'
slug: okf-summary
n: 1
outcome_written: false
---

# Spike okf-summary/1

does a commit-order freshness rule (concepts changed after the last commit to .okf/summary.md, or uncommitted while the summary is not) flag the right concepts across same-commit, uncommitted, kmctl verify, log/index/handoff and ack edits, and run fast on kmctl?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-sum1/freshness.py
```

## Outcome

Not written yet: `loopctl plan spike-note okf-summary 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/freshness.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-sum1/freshness.py`, which the command used
