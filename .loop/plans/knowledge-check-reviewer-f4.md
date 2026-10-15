---
type: plan
title: 'Plan: knowledge-check-reviewer-f4'
description: Deferred hardening from knowledge-check, reviewer finding f4 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:38:18+00:00'
slug: knowledge-check-reviewer-f4
status: draft
epic: cli
depends_on: []
priority: null
---

# knowledge-check-reviewer-f4

Relayed from: knowledge-check, reviewer finding f4 in review round 1

## Intent

index.read_text() uses the locale encoding and raises on a non-UTF-8 index, so kmctl check crashes with a UnicodeDecodeError traceback. cli-interface.md requires a one-line stderr refusal and a nonzero exit, or the bad file could be reported as a finding. Use encoding="utf-8" and handle the decode error. Non-blocking because the fix is local. at src/kmctl/checks.py:40.

## Could invalidate this plan

- none
