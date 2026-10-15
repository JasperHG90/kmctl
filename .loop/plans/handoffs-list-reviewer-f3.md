---
type: plan
title: 'Plan: handoffs-list-reviewer-f3'
description: Deferred hardening from handoffs-list, reviewer finding f3 in review round 2.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:42:15+00:00'
slug: handoffs-list-reviewer-f3
status: draft
epic: cli
depends_on: []
priority: null
---

# handoffs-list-reviewer-f3

Relayed from: handoffs-list, reviewer finding f3 in review round 2

## Intent

the new astimezone(UTC) call raises OverflowError for a datetime at the edge of the range, such as 0001-01-01T00:00:00+01:00, and the command crashes with a traceback at src/kmctl/okf.py:43.

## Could invalidate this plan

- none
