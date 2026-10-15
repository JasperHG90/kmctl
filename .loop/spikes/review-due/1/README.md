---
type: spike
title: Spike review-due/1
description: can every OKF sources[].resource be classified as URL, concept or tracked repository path by a simple rule?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:13:36+00:00'
slug: review-due
n: 1
outcome_written: true
---

# Spike review-due/1

can every OKF sources[].resource be classified as URL, concept or tracked repository path by a simple rule?

The command exited 1:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-review-due/classify_sources.py /home/vscode/workspace
```

## Outcome

In the workspace bundle, 4 of 94 concepts have `sources`, with 11 entries in all: 2 URLs, 2 tracked repository paths, 0 concept ids and 7 the rule could not classify. None matched more than one class.
All 7 look like repository paths but name files that are not in this repository and never were: 6 carry an old repo prefix (`loop-harness-plugin/...`) and 1 (`.loop/verdicts/...`) is a file from a downstream repository. Even with the prefix removed, only `plugin/hooks/hooks.json` is tracked.
So "has a URL scheme" and "is in `git ls-files`" tell the kinds apart without overlap. What is not reliable is "looks like a path": spec section 6.2 allows bundle-relative and concept-relative paths and free-text scope descriptors, and the real bundle uses repo-root paths, some of them dead.
Risk 1 is real but narrow. Check git only for entries `git ls-files` lists, and report untracked path-like entries as their own case instead of skipping them silently.
Limit: one bundle, 11 entries, no concept-id sources in the sample.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/classify_sources.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-review-due/classify_sources.py`, which the command used
