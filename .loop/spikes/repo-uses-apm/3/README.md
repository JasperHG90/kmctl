---
type: spike
title: Spike repo-uses-apm/3
description: does APM 0.33.0 install all 13 rules and 3 skills from jasperhg90/skills at f0813cd with paths scoping equal to upstream applyTo, bodies equal to upstream, and skills byte for byte
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T17:52:19+00:00'
slug: repo-uses-apm
n: 3
outcome_written: true
---

# Spike repo-uses-apm/3

does APM 0.33.0 install all 13 rules and 3 skills from jasperhg90/skills at f0813cd with paths scoping equal to upstream applyTo, bodies equal to upstream, and skills byte for byte

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/spike3.sh
```

## Outcome

APM 0.33.0 installed all 16 items (13 rules, 3 skills) from jasperhg90/skills pinned to f0813cd, which is also upstream main today; the lock records that commit for all 16. Every rule landed as `.claude/rules/<name>.md`; its `paths:` list equals upstream `applyTo` (7 scoped rules), and the 6 rules with no `applyTo` got no front matter. Every body equals upstream (body = text after front matter, leading blank lines removed, since APM drops the blank line along with a removed block). All 3 skills match upstream byte for byte. Exit 0.
Against kmctl's aim-installed files today: `paths:` is unchanged for all 13, and `name`/`description` (`title` in 2 rules) are dropped. 11 bodies are unchanged. pre-existing-issues loses a stray `%   ` after its last `</constraint>`. python-testing loses about 50 lines (the "Test tiers" section and the measure-before-marking, run-your-own-test and every-tier-runs-somewhere constraints), and that text is in no upstream commit, so it is a local edit that APM would drop. Skill rule-creator changes upstream (README now describes `applyTo`/apm); agent-creator and generate-art are unchanged.
Settles risk 1 for install, placement, scoping and bodies. It also shows something the plan does not cover: the local python-testing text has to go upstream (or be kept some other way) before the switch.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike3.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/spike3.sh`, which the command used
