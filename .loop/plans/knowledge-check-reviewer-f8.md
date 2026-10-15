---
type: plan
title: 'Plan: knowledge-check-reviewer-f8'
description: Deferred hardening from knowledge-check, reviewer finding f8 in review round 2.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:41:44+00:00'
slug: knowledge-check-reviewer-f8
status: draft
epic: cli
depends_on: []
priority: null
---

# knowledge-check-reviewer-f8

Relayed from: knowledge-check, reviewer finding f8 in review round 2

## Intent

When .okf/index.md is not UTF-8, check_okf sets linked to an empty set, so every section is also reported as "section is not linked from .okf/index.md". Those findings are noise behind the one real cause. Skip the unlinked-section findings when the root index cannot be read. Non-blocking - the real cause is still reported and the exit code is right. at src/kmctl/checks.py:181.

## Could invalidate this plan

- none
