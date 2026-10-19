---
type: spike
title: Spike antigravity-apm-audit/2
description: on a fresh clone of a committed claude+antigravity kmctl install, does apm install --frozen plus kmctl plugin patch leave git status --porcelain empty, and does a committed hand edit under .agents/skills/ make it non-empty?
tags:
- spike
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:33:52+00:00'
slug: antigravity-apm-audit
n: 2
outcome_written: true
---

# Spike antigravity-apm-audit/2

on a fresh clone of a committed claude+antigravity kmctl install, does apm install --frozen plus kmctl plugin patch leave git status --porcelain empty, and does a committed hand edit under .agents/skills/ make it non-empty?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-audit-r3/gate2.sh
```

## Outcome

Setup: kmctl 0.10.0 at baf863e8, served by file:// insteadOf, installed by apm 0.33.0 for claude+antigravity, then `kmctl plugin patch`. 96 tracked files (47 under .agents, 45 under .claude), apm_modules/ gitignored. On a fresh clone of that commit, `apm install --frozen` + `kmctl plugin patch` left `git status --porcelain` empty: no timestamp, ordering or absolute-path drift. A committed one-line edit to .agents/skills/architecture-review/SKILL.md, checked out fresh, showed as ` M` after the gate.
This settles risk 3 for the CI case: a clean checkout of committed files.
Limit: an *uncommitted* edit in the working tree is not caught. `apm install --frozen` writes the locked bytes back over it without a word (afterwards only .agents/hooks.json shows ` M`, and patch then restores it), so porcelain ends up empty. A test that edits a file and runs the gate in the same checkout will see exit 0 unless it commits the edit and clones first.
One run, one package, project scope only, and okf-skills fetched from real GitHub.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/gate2.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/c37be586-8598-4232-be34-7d43e553b1d7/scratchpad/spike-audit-r3/gate2.sh`, which the command used
