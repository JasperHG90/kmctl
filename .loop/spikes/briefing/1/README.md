---
type: spike
title: Spike briefing/1
description: do the docs-layout and okf-bundle constraints fit a 500-word briefing with routing and state?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:12:32+00:00'
slug: briefing
n: 1
outcome_written: true
---

# Spike briefing/1

do the docs-layout and okf-bundle constraints fit a 500-word briefing with routing and state?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-briefing/count_rules.py
```

## Outcome

The 8 constraints in `docs-layout.md` and `okf-bundle.md` come to 506 words with their WHY lines and 339 without (words counted as loopctl counts them, `len(line.split())`). The two whole rule files are 1084.
With an 80-word routing block and a 40-word state block, the briefing is 626 words with WHY (over the 500 budget) and 459 without (41 to spare). For comparison, `loopctl briefing` prints 281 words in this repo.
So the rules fit inline only without their WHY lines. That rules out the `kmctl rules NAME` shape change for these two rule files, and it settles risk 1 as long as the generalized rules stay about this length. The 41-word margin is thin. Limits: routing and state were assumed sizes, not real drafts, and the shipped rules will be rewritten from these.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/count_rules.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-briefing/count_rules.py`, which the command used
