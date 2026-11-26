---
type: spike
title: Spike okf-vs-change-audit/2
description: does a checkout of refs/pull/N/merge with fetch-depth 0 and no persisted credentials have origin/BASE for a base worktree, and does a three-dot diff against it list exactly the PR files, also when main moved?
tags:
- spike
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T13:16:35+00:00'
slug: okf-vs-change-audit
n: 2
outcome_written: true
---

# Spike okf-vs-change-audit/2

does a checkout of refs/pull/N/merge with fetch-depth 0 and no persisted credentials have origin/BASE for a base worktree, and does a three-dot diff against it list exactly the PR files, also when main moved?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-cvc-r3/checkout_pr.sh
```

## Outcome

The script copied actions/checkout v7.0.1's fetch-depth 0 steps for a pull request, read from its source at 3d3c42e (`getRefSpecForAllHistory`, `getCheckoutInfo`, `fetch`): `fetch --no-tags --prune` with `+refs/heads/*:refs/remotes/origin/*`, `+refs/tags/*:refs/tags/*` and `+$GITHUB_SHA:refs/remotes/pull/1/merge`, then `checkout --force refs/remotes/pull/1/merge`. It ran against a local bare repo standing in for GitHub. All 18 checks passed in 3 scenarios: no base movement, main moved before the merge ref was made, and main moved again after it.
(a) `origin/main` is always there. `git worktree add --detach DIR origin/main` works with the remote URL deliberately broken, so it needs no token and no network. knowledge-ci.sh's `rev-parse` check passes, so its fallback fetch never runs.
(b) `git diff --name-only origin/main...HEAD` listed exactly the PR's 3 files every time, never main's own changes. This settles risk 3.
Limits: this was a local stand-in, not a run on GitHub, and the token-free fetch that checkout itself makes was not tested. When main moves after the merge ref is made, the base tree is the newer main tip, not `HEAD^1`. The file list is still right.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/checkout_pr.sh`: a copy of `/tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-cvc-r3/checkout_pr.sh`, which the command used
