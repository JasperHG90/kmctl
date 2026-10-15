---
type: plan
title: 'Plan: briefing'
description: "kmctl briefing prints one context block that combines where knowledge lives, what is due for review and the rules for writing knowledge, under a word budget (ADR 0002, I3)."
slug: briefing
epic: cli
depends_on: [adapt-copied-rules]
priority: 2
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:19+00:00'
---

# briefing

Relayed from: none

## Intent

`kmctl briefing` prints the block the SessionStart hook injects (ADR 0002). It has three parts:

- routing: where each kind of knowledge lives (`docs/` by Diataxis, `.okf/` and its sections, skills, rules) and which skill to use for what;
- state: how many concepts are due for review and the live handoffs, once `review-due` lands (until then the part is omitted);
- rules: the knowledge-management rules, shipped as package data in `new:src/kmctl/rules/` and generalized from `.claude/rules/docs-layout.md` and `.claude/rules/okf-bundle.md`.

It reads and never writes, works in a repository with no `.okf/` (it then says how to start one), and stays under a word budget a test checks (I3). `--json` prints the same as one object.

Done when the briefing prints in this repository and in an empty one, and a test fails when it exceeds the budget.

## Could invalidate this plan

- The rules may not fit the word budget together with routing and state. If they do not, the briefing has to name rules by title and print one on demand (`kmctl rules NAME`), which changes the shape of the command. Settled by spike:briefing/1: the two rule files' constraints come to 339 words without their WHY lines (506 with), so with routing and state the briefing is about 459 words, inside a 500-word budget. The briefing carries each constraint without its WHY line.
