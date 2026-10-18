---
type: spike
title: Spike starter-in-repo/1
description: does copier render a root copier.yml with _subdirectory starter from the newest tag of a repo whose older tags have no copier.yml, without copying the repo root files?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T09:54:15+00:00'
slug: starter-in-repo
n: 1
outcome_written: true
---

# Spike starter-in-repo/1

does copier render a root copier.yml with _subdirectory starter from the newest tag of a repo whose older tags have no copier.yml, without copying the repo root files?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike1/spike.sh
```

## Outcome

copier 9.19.1, run on a local clone of kmctl (tags v0.2.0 to v0.5.1, none with copier.yml) plus a commit tagged v0.6.0 that adds a root copier.yml with `_subdirectory: starter` and kmctl-starter's template under starter/.
With no --vcs-ref, copier picked v0.6.0 (`_commit: v0.6.0`), rendered all 9 template files with apm.yml `targets: [opencode]`, and copied none of kmctl's root files (no src/, pyproject.toml, tests/, action.yml, copier.yml, starter/; README.md is the rendered template's). It gave no warning about the older tags without copier.yml.
With `--vcs-ref HEAD` on a dirty clone, copier warned `DirtyLocalWarning: Dirty template changes included automatically`, used both a modified and an untracked file, and recorded `_commit: v0.6.0-1-g66d40d86`. With no --vcs-ref on the same dirty clone it used clean v0.6.0.
Settles risk 1: the layout works. Limit: local path source only, not gh: or https; one tag carrying copier.yml.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike1/spike.sh`, which the command used
