---
type: plan
title: 'Plan: harness-prompt-reviewer-f1'
description: Deferred hardening from harness-prompt, reviewer finding f1 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:08:02+00:00'
slug: harness-prompt-reviewer-f1
status: draft
epic: null
depends_on: []
priority: null
---

# harness-prompt-reviewer-f1

Relayed from: harness-prompt, reviewer finding f1 in review round 1

## Intent

_read_answer tests word.isdigit() and then calls int(word). Characters like '²' pass isdigit() but int() rejects them, so an answer such as '²' ends the command with a ValueError traceback instead of asking again. at src/kmctl/__init__.py:777. The fix reads a word as a number only when
`word.isdecimal()`, so any other word is taken as a name and asked again.

It worked when an answer of `²` is asked again (a test in
`tests/test_plugin.py`).

## Could invalidate this plan

- none
