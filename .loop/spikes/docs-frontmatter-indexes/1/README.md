---
type: spike
title: Spike docs-frontmatter-indexes/1
description: 'does prek 0.5.5 install and run a language: python kmctl hook from a local path repo pinned to a commit of this checkout, how long does it take, and do args like --version pass through?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T16:46:27+00:00'
slug: docs-frontmatter-indexes
n: 1
outcome_written: true
---

# Spike docs-frontmatter-indexes/1

does prek 0.5.5 install and run a language: python kmctl hook from a local path repo pinned to a commit of this checkout, how long does it take, and do args like --version pass through?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/861afc8c-df0a-45c2-b2d5-2163f49b7f9d/scratchpad/spike-prek/prek_local_repo.sh
```

## Outcome

prek 0.5.5 installed kmctl as a `language: python` hook from a local path repo (a clone of HEAD dd3a0ec plus a committed `.pre-commit-hooks.yaml`, pinned by sha) and ran `kmctl check` in a second repo: Passed. The first run, with an empty PREK_HOME, took about 2 s; reruns about 0.1 s each. The whole spike took 2.6 s, far under the 1800 s gate.
Args pass through: `entry: kmctl` with `args: [--version]` printed `kmctl 0.3.0`, and `args: [--json]` on `entry: kmctl check` printed the JSON findings.
This settles risk 1. Limit: the uv cache was warm, so a cold CI runner pays extra to download kmctl's dependencies. The consumer repo had no docs/ or .okf/, so the checks were skipped, not exercised.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/prek_local_repo.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/861afc8c-df0a-45c2-b2d5-2163f49b7f9d/scratchpad/spike-prek/prek_local_repo.sh`, which the command used
