---
type: spike
title: Spike init-seeds-the-habit/1
description: does seeding rules, a CLAUDE.md kmctl block and decision 0001 make an agent building a FastAPI app record more decisions and architecture pages than kmctl init plus the briefing alone
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:02:50+00:00'
slug: init-seeds-the-habit
n: 1
outcome_written: true
---

# Spike init-seeds-the-habit/1

does seeding rules, a CLAUDE.md kmctl block and decision 0001 make an agent building a FastAPI app record more decisions and architecture pages than kmctl init plus the briefing alone

The command exited 0:

```
SPIKE_BASE=/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-seed/runs /usr/bin/python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-seed/driver.py
```

## Outcome

Ran 3 fresh repos per arm with one FastAPI quiz task (claude -p, Opus 5.5). Arm A got kmctl init plus the briefing. Arm B also got the four rule files, a CLAUDE.md kmctl block, a filled decision 0001 and the next-steps text. B beat A on both counts: decisions written 4.33 vs 3.00 (A 4/2/3, B 4/5/4) and architecture pages 1.00 vs 0.00 (A 0/0/0, B 1/1/1, each with mermaid and a Depicts section). Every new decision in both arms names a rejected alternative. Both arms filled the manifesto purpose 3/3 and passed `kmctl check` 3/3, and all 6 apps' tests pass. Log lines added: A 3 to 6, B 7 to 8.

This settles risk 1 for this setup: seeding moves both counts, and moves architecture pages from none to one. Arm A did not reproduce the operator's failure (1 decision of 6 choices), so the decision gap is small. The clearest gain is architecture pages.

Limits: N=3 per arm, one task, one model. The briefing went in the prompt text, not through a real SessionStart hook, so it may have weighed more there than a hook's output would. Both arms ran under the operator's login, so the global ~/.claude/CLAUDE.md and the user-level okf plugin loaded in both (its Stop hook stays dormant without `upkeep: enforced`). The kmctl plugin is project-scoped to the kmctl checkout, so it did not inject a second briefing. The rule files were copied from this repo, loopctl mentions included. "Names a rejected alternative" is a keyword match; one record was checked by hand.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/driver.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-seed/driver.py`, which the command used
