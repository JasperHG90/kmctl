---
type: eval
title: 'Eval: briefing'
description: 'Definition of done for briefing: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:50:14+00:00'
slug: briefing
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 46fbe74e43c95f67c7ff01be2c7e6c3e3812b41d02befaa270b99ca1a219c3ec
  at: '2026-10-15T10:50:14+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl briefing prints routing, state and the knowledge rules in a repository with docs/ and .okf/.
  Fails when: any of the three parts is missing from the output
- r2: State shows counts only: concepts due, live handoffs, and the newest handoff's title.
  Fails when: the state part lists concept names, or a count disagrees with review due or kmctl handoffs on the fixture
- r3: The briefing stays within 600 words.
  Fails when: len(output.split()) exceeds 600 on the fixture with due concepts and handoffs
- r4: In a repository with no .okf/ the briefing says how to start one and exits 0.
  Fails when: it exits nonzero, or does not name kmctl init
- r5: The briefing reads and never writes.
  Fails when: any file in the fixture repository changes after a run
- r6: --json prints the same content as one object.
  Fails when: stdout is not one JSON object with routing, state and rules
