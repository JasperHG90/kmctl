---
type: spike
title: Spike init-claude-md-always/3
description: on the toml-parser and job-queue scaffolds, does an agent record more decisions and architecture pages with the new kmctl init and plugin than with kmctl before init-seeds-the-habit, measured in the worktree the agent used
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T17:28:52+00:00'
slug: init-claude-md-always
n: 3
outcome_written: true
---

# Spike init-claude-md-always/3

on the toml-parser and job-queue scaffolds, does an agent record more decisions and architecture pages with the new kmctl init and plugin than with kmctl before init-seeds-the-habit, measured in the worktree the agent used

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/smoke-scenarios/driver.py
```

## Outcome

Scaffolds 01-toml-parser and 03-job-queue-simulation (loop bullets cut from AGENTS.md), claude -p Opus 5.5, N=2 per scenario per arm. NEW: kmctl from the init-claude-md-always worktree (block in AGENTS.md, CLAUDE.md = `@AGENTS.md`, rules, 0001) and its plugin. OLD: kmctl at a3095ed, before init-seeds-the-habit, and its plugin. Prompt: init's stdout, then "Read MANIFESTO.md and AGENTS.md, then build the first milestone of the roadmap. Work until its tests pass." Measured in the checkout the agent used (2 OLD runs worked in a git worktree).

| run | decisions (named a rejected option) | arch pages | .okf purpose / invariants | log lines | kmctl check | tests | time, cost |
|---|---|---|---|---|---|---|---|
| NEW 01-1 | 2 (2) | 1 | yes / yes | 5 | pass | 6 pass | 116 s, $0.64 |
| NEW 01-2 | 2 (2) | 1 | yes / yes | 5 | pass | 3 pass | 93 s, $0.58 |
| NEW 03-1 | 2 (2) | 1 | yes / yes | 5 | pass | 2 pass | 113 s, $0.59 |
| NEW 03-2 | 2 (2) | 1 | yes / yes | 5 | pass | 1 pass | 102 s, $0.66 |
| OLD 01-1 | 0 | 0 | no / no | 0 | pass | 2 pass | 114 s, $0.43 |
| OLD 01-2 | 0 | 0 | no / no | 0 | pass | 3 pass | 74 s, $0.44 |
| OLD 03-1 | 0 | 0 | no / no | 0 | pass | 1 pass | 71 s, $0.38 |
| OLD 03-2 | 0 | 0 | no / no | 0 | pass | 1 pass | 69 s, $0.48 |

NEW means 2.0 decisions and 1.0 architecture pages against OLD's 0 and 0, so exit 0. Every NEW transcript holds the kmctl block's duties text (it reached the model through CLAUDE.md's `@AGENTS.md`) and shows `kmctl new decision` and `kmctl check` calls; no OLD run ran `kmctl new` at all. Two manifestos: no run edited the root MANIFESTO.md. All 4 NEW runs filled .okf/manifesto.md as a summary that names the root MANIFESTO.md as the binding spec ("where the two disagree, MANIFESTO.md wins"), copied its invariants with a status column, and left Values empty for the operator. All 4 OLD runs left .okf/manifesto.md as the empty template, so MANIFESTO.md stayed the only spec.

Limits: N=2 per cell, one model. The first milestone is Phase 0, a smoke test, so runs took 1 to 2 minutes and few choices came up; a longer milestone could change the counts. The "rejected" count is a keyword match. loopctl was on PATH from ~/.local/bin and Phase 0 asks for it, so every run also ran `loopctl init`, and some decisions are about loopctl gates. The global ~/.claude/CLAUDE.md and user-level plugins loaded. Spike 2 is the same run mismeasured.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/driver.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/smoke-scenarios/driver.py`, which the command used
