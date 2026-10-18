---
type: spike
title: Spike okf-summary/2
description: can the briefing say "Start at .okf/summary.md" and whether the summary is current within 500 tokens in the worst-case test, and which ROUTING words must go?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T19:42:47+00:00'
slug: okf-summary
n: 2
outcome_written: true
---

# Spike okf-summary/2

can the briefing say "Start at .okf/summary.md" and whether the summary is current within 500 tokens in the worst-case test, and which ROUTING words must go?

The command exited 0:

```
uv run --project /home/vscode/kmctl python /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-sum2/fit.py
```

## Outcome

It fits. The worst-case briefing (`test_briefing_long_handoff_title_keeps_the_budget`'s repo) is 494/500 tokens today. Swapping in "Start at .okf/summary.md" alone gives 495, then 499 with "; summary current" and 504 with "; summary behind: 3 concepts changed" on the state line, so a swap alone breaks the budget.
Dropping the Diataxis list "(tutorials, how-to, reference, explanation)" from the docs/ line fixes it: 484 with no status, 488 current, 493 behind (also 493 with a 3-digit count). The Verbs line already names the four types (`kmctl new doc tutorial|how-to|reference|explanation`), so no information is lost. This repo goes 474 -> 473 at most.
Adding ", then index.md" after summary.md costs 4 more tokens (497 worst), which still fits but leaves only 3 spare.
This settles risk 2. Limits: sizes use estimate_tokens (4 chars per token) on the CLI output, as the tests do. The status wording was spliced onto the rendered state line, not built by render(). The worst-case repo has no summary.md yet, and init's skeleton could add one due concept (the count changes, the size does not).

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/fit.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-sum2/fit.py`, which the command used
