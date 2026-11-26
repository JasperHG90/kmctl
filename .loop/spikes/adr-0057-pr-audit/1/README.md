---
type: spike
title: Spike adr-0057-pr-audit/1
description: does kmctl review due --base list every stable decision whose sources a merged pull request changed, including folder sources (ADR 0046 packages/kmctl/) and decisions with no verified entry?
tags:
- spike
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T12:53:02+00:00'
slug: adr-0057-pr-audit
n: 1
outcome_written: true
---

# Spike adr-0057-pr-audit/1

does kmctl review due --base list every stable decision whose sources a merged pull request changed, including folder sources (ADR 0046 packages/kmctl/) and decisions with no verified entry?

The command exited 1:

```
/home/vscode/workspace/.venv/bin/python /tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-r2/pr_scope.py 15
```

## Outcome

Over the last 15 first-parent merges on main, a plain `sources` matcher (file, or folder as prefix) found 82 stable-decision hits; `kmctl review due --base FIRST_PARENT` listed 34 of them and **none for a `source changed` reason**: all 34 were listed as `unverified` only because the PR edited the record itself. The 48 misses all have the same cause: no stable decision on main has a `verified` entry (0 of 49), and `review_due.py` compares sources only for concepts with `verified`, so an unverified decision's sources are never checked and `--base` keeps `unverified` only for a page the branch changed.
ADR 0046's folder source `packages/kmctl/` matched in 4 PRs and was never listed. No folder-source or unverified decision was ever listed because of a source change.
The risk holds: scoping on `review due --base` misses every decision whose sources a PR changed, as the decision log stands today. Limit: the path for verified decisions (source changed after the verification commit) went untested, because no decision is verified. stdout.txt is cut at 20 kB (the oldest PRs' lines are lost); the totals at the end are complete.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/pr_scope.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-r2/pr_scope.py`, which the command used
