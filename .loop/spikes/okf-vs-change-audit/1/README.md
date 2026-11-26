---
type: spike
title: Spike okf-vs-change-audit/1
description: 'can GITHUB_TOKEN with pull-requests: write but no issues: write list, create and edit a pull request comment (issues/{n}/comments, issues/comments/{id})?'
tags:
- spike
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T13:16:07+00:00'
slug: okf-vs-change-audit
n: 1
outcome_written: true
---

# Spike okf-vs-change-audit/1

can GITHUB_TOKEN with pull-requests: write but no issues: write list, create and edit a pull request comment (issues/{n}/comments, issues/comments/{id})?

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-cvc-r2/check_pr_comment_perms.py
```

## Outcome

GitHub's "Permissions required for GitHub Apps" page (which the workflow-syntax docs name as the source for GITHUB_TOKEN's `pull-requests` key) lists all three endpoints under "Pull requests": `GET .../issues/{n}/comments` (read), `POST .../issues/{n}/comments` (write) and `PATCH .../issues/comments/{id}` (write). The ✓ in "Additional permissions" means any one of a set works, here Issues or Pull requests. So `pull-requests: write` without `issues: write` is enough to list, create and edit by id the PR comment, and the ADR's permission can stay as it is.
Settles risk 2. Limit: this rests on the docs as fetched on 2026-11-26, not a live Actions run (`gh` was not authenticated), so the first real workflow run on a PR is the true test.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/check_pr_comment_perms.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/spike-cvc-r2/check_pr_comment_perms.py`, which the command used
