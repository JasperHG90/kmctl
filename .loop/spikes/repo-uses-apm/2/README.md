---
type: spike
title: Spike repo-uses-apm/2
description: does APM 0.33 install a jasperhg90/skills rule to .claude/rules/ with its front matter intact and a skill to .claude/skills/
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T17:49:00+00:00'
slug: repo-uses-apm
n: 2
outcome_written: true
---

# Spike repo-uses-apm/2

does APM 0.33 install a jasperhg90/skills rule to .claude/rules/ with its front matter intact and a skill to .claude/skills/

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/spike.sh
```

## Outcome

APM 0.33.0 (pip `apm-cli`) installed jasperhg90/skills at f0813cd (the commit that renamed `rules/*.md` to `*.instructions.md` with `applyTo`; it has no apm.yml, and APM takes single files and SKILL.md folders anyway). With `targets: [claude]`, `rules/X.instructions.md` landed as `.claude/rules/X.md` and the skill landed as `.claude/skills/generate-art/`, byte for byte. Exit 1: APM rewrites rule front matter, so it is not byte for byte. `applyTo: "**/*.py"` became a `paths:` YAML list and `name`/`description` were dropped. A rule with no `applyTo` lost its whole front matter block.
A plain `rules/X.md` path (what aim installs today, with `paths:`) is refused: "Individual files must end with .prompt.md, .instructions.md, .agent.md". Older pins such as f10a341 have no `.instructions.md` files, so the pin must be f0813cd or later. Pins resolve to a full SHA in `apm.lock.yaml`, which also records per-file sha256 hashes.
Install wrote no AGENTS.md or CLAUDE.md; it added `apm_modules/` to .gitignore. `apm compile` (target claude) writes nothing because Claude reads .claude/rules/. `apm compile -t agents` builds AGENTS.md (plus .github/copilot-instructions.md) from the instruction bodies, but never overwrites a hand-written AGENTS.md.
Settles risk 1 partly. Install and placement work, and Claude-usable `paths:` scoping survives. The risk is real only if byte-for-byte front matter (`name`/`description`) matters to the plan. Tested 2 rules and 1 skill.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/spike.sh`, which the command used
