---
type: spike
title: Spike starter-in-repo/5
description: do uv and APM 0.33.0 follow a git url.insteadOf rewrite of https://github.com/JasperHG90/kmctl to a file:// bare repo of this checkout tagged at its version?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T09:58:22+00:00'
slug: starter-in-repo
n: 5
outcome_written: true
---

# Spike starter-in-repo/5

do uv and APM 0.33.0 follow a git url.insteadOf rewrite of https://github.com/JasperHG90/kmctl to a file:// bare repo of this checkout tagged at its version?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike2/spike.sh
```

## Outcome

With a scratch HOME, no GitHub tokens, and GIT_CONFIG_GLOBAL holding `[url "file:///SCRATCH/srv/o/kmctl.git"] insteadOf = https://github.com/JasperHG90/kmctl.git` plus `insteadOf = https://github.com/JasperHG90/kmctl`, all three came from a bare clone of this checkout tagged v0.5.1.
(a) `uv tool install --force git+https://github.com/JasperHG90/kmctl@v0.5.1` and (b) `uvx --from` it installed kmctl 0.5.1 with a marker file only the served copy has (direct_url.json keeps the github.com URL and the served commit). (c) `uvx --from apm-cli==0.33.0 apm install` (targets [claude]) exited 0, and apm.lock.yaml records host github.com, resolved_ref v0.5.1, resolved_commit = the served commit. No GitHub API call was needed.
APM 0.33.0 allows a rewrite to file:// (not a network host) but refuses http:// and cross-host rewrites (spike:starter-in-repo/4), so no git server is needed. Both insteadOf forms are needed: the justfile URL has no .git, apm.yml has .git; git picks the longest match.
Settles risk 2. Limit: the transitive okf-skills dependency still came from real GitHub (public); one run, one tag.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike2/spike.sh`, which the command used
