---
type: spike
title: Spike verify-verb/1
description: does naming kmctl verify on the briefing state line keep the briefing under its 500-token budget, in this repo and the test worst cases?
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T21:20:40+00:00'
slug: verify-verb
n: 1
outcome_written: true
---

# Spike verify-verb/1

does naming kmctl verify on the briefing state line keep the briefing under its 500-token budget, in this repo and the test worst cases?

The command exited 1:

```
uv run --project /home/vscode/kmctl python /tmp/claude-1000/-home-vscode-kmctl/125ee49d-9032-42f6-96bc-67af67c66263/scratchpad/spike-verify-verb/budget.py
```

## Outcome

The risk is real. The CLI briefing is 474/500 tokens in this repo, but already 488 in `test_briefing_token_budget`'s repo and 494 in `test_briefing_long_handoff_title_keeps_the_budget`'s (the test asserts < 500).
Appending even the shortest sentence (" Checked one? kmctl verify ID --by human:ID.", 44 chars) gives 485 here but 499 and 505 in the two test cases. The 67-char wording gives 490/504/511; a 116-char one gives 503/517/523.
Changing the pointer in place fits only just: "(kmctl review due; kmctl verify)" gives 477/491/498, and "(kmctl review due, then kmctl verify ID)" gives 479/493/500, which fails the worst-case test.
So the state line can name the verb in at most about 20 extra characters, with 2 tokens to spare in the worst case. Any `--by human:ID` usage hint has to live in the rule and skill, unless other briefing text is cut. Sizes use estimate_tokens (4 chars per token), as the tests do.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/budget.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/125ee49d-9032-42f6-96bc-67af67c66263/scratchpad/spike-verify-verb/budget.py`, which the command used
