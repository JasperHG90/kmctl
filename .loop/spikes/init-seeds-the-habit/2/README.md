---
type: spike
title: Spike init-seeds-the-habit/2
description: does the built kmctl init with the real SessionStart hook briefing get an agent building a FastAPI app to record decisions and architecture pages at least as well as spike 1, rerun of spike 1 task with one arm
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:24:37+00:00'
slug: init-seeds-the-habit
n: 2
outcome_written: true
---

# Spike init-seeds-the-habit/2

does the built kmctl init with the real SessionStart hook briefing get an agent building a FastAPI app to record decisions and architecture pages at least as well as spike 1, rerun of spike 1 task with one arm

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-seed-r7/driver.py
```

## Outcome

Reran spike 1's FastAPI quiz task (claude -p, Opus 5.5, N=3) with one arm: the built worktree's `kmctl init` (four rule files, the CLAUDE.md kmctl block, decision 0001 and its next-steps line, whose real stdout went in the prompt as what setup printed) and the briefing delivered by the worktree plugin's real SessionStart hook, loaded with `claude --plugin-dir <worktree>/plugin`. A probe run first confirmed the hook's `kmctl briefing` output reaches the model.

| | mean decisions | runs with an architecture page | kmctl check | tests |
|---|---|---|---|---|
| r7, built init + real hook | 4.67 (5/5/4) | 3/3 | 3/3 | 3/3 pass |
| spike 1 arm A, init + briefing in prompt | 3.00 (4/2/3) | 0/3 | 3/3 | 3/3 pass |
| spike 1 arm B, hand seeding + briefing in prompt | 4.33 (4/5/4) | 3/3 | 3/3 | 3/3 pass |

Decisions count only records beyond init's 0001. Every new decision names a rejected alternative (keyword match). Each run wrote one architecture page with a mermaid diagram and a Depicts section, filled the manifesto purpose, and kept one kmctl block in CLAUDE.md. The built init holds spike 1's gain: architecture pages 3 of 3, and decisions above arm A and on par with arm B.

Limits: N=3, one task, one model. The plugin loaded through `--plugin-dir`, not `kmctl plugin install --scope project`. A project-scope install from a scratch repo would re-register the `kmctl` marketplace in the operator's user-level Claude config under a different path, and isolating the config dir would mean copying login credentials, so neither was done. The hook and its command are the same either way. The global ~/.claude/CLAUDE.md and the user-level okf plugin loaded, as in spike 1. After the spike started, one warning message in scaffold.py changed (broken-marker text); setup had already run, and the change does not affect this task.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/driver.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-seed-r7/driver.py`, which the command used
