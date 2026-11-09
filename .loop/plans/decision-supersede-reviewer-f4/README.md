---
type: plan
title: 'Plan: decision-supersede-reviewer-f4'
description: Deferred hardening from decision-supersede, reviewer finding f4 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:56:03+00:00'
slug: decision-supersede-reviewer-f4
status: draft
epic: cli
depends_on: []
priority: null
---

# decision-supersede-reviewer-f4

Relayed from: decision-supersede, reviewer finding f4 in review round 1

## Intent

_number uses str.isdigit, which accepts Unicode digits such as "²"; int() then raises ValueError and the CLI prints a traceback instead of a refusal. at src/kmctl/supersede.py:27.

## Could invalidate this plan

- none
