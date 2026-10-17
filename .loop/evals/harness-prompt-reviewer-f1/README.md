---
type: eval
title: 'Eval: harness-prompt-reviewer-f1'
description: 'Definition of done for harness-prompt-reviewer-f1: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:17:13+00:00'
slug: harness-prompt-reviewer-f1
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: f13b4fc1b03bbe9af283ec9397c6a4ae323d9d1c711f1e7cdc2225e7598f81ed
  at: '2026-10-17T06:17:13+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: At the harness question, an answer that is a digit character but not a decimal number, such as '²', is asked again naming the accepted values, and the next valid answer installs; the command never ends with a traceback.
  Fails when: the answer '²' ends the command with an exception or a nonzero exit, or is not asked again
- r2: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
