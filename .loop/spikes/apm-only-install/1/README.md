---
type: spike
title: Spike apm-only-install/1
description: does an APM 0.33.0 package apm/apm.yml with skills, agent and instructions under apm/.apm/ and no git parent deliver the agent and skills byte for byte and the rules with paths intact, and does apm install PACKAGE --target claude work in a repo with no apm.yml
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T19:51:27+00:00'
slug: apm-only-install
n: 1
outcome_written: true
---

# Spike apm-only-install/1

does an APM 0.33.0 package apm/apm.yml with skills, agent and instructions under apm/.apm/ and no git parent deliver the agent and skills byte for byte and the rules with paths intact, and does apm install PACKAGE --target claude work in a repo with no apm.yml

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-apm-r2/spike-layout.sh
```

## Outcome

A: the planned layout (apm/apm.yml with only the pinned okf-skills dependency, no `git: parent`; skills, agent and 4 `*.instructions.md` under apm/.apm/), served from a local git server and listed in a consumer apm.yml as `{git, path: apm}`, installs with exit 0. All 7 kmctl skills and kmctl-auditor.md land byte for byte; all 4 rules land in `.claude/rules/` with `paths:` equal to today's (a comma-joined `applyTo`, up to 6 globs) and bodies equal; okf's 4 skills land too. So the agent is not dropped once it sits under `.apm/agents/`.
B: in a git repo with no apm.yml, `apm install JasperHG90/Knowledge-management/apm#v0.3.0 --target claude` exits 0, creates apm.yml (listing the package, `targets: [claude]`) and deploys the 7 skills and the agent. That was the released v0.3.0, which still has the old layout; the CLI form cannot point at a subfolder of a repo on a local, non-GitHub server ("use an explicit git: + path: entry in apm.yml"), so B was not run against the new layout.
Settles risk 2. Two things the plan should know: `apm install PACKAGE` writes an apm.yml (and apm.lock.yaml) into the user's repository; and the integration test cannot use the CLI form against the served tree, so it needs a consumer apm.yml entry, or `kmctl plugin install` has to write one.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-layout.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-apm-r2/spike-layout.sh`, which the command used
