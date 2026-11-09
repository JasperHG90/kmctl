---
type: plan
title: 'Plan: scaffold-init-reviewer-f5'
description: Deferred hardening from scaffold-init, reviewer finding f5 in review round 3.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:40:48+00:00'
slug: scaffold-init-reviewer-f5
status: draft
epic: cli
depends_on: []
priority: null
---

# scaffold-init-reviewer-f5

Relayed from: scaffold-init, reviewer finding f5 in review round 3

## Intent

a kept index.md or log.md that is not valid UTF-8 makes init crash with a UnicodeDecodeError traceback after it has written the other files at src/kmctl/scaffold.py:87.

## Could invalidate this plan

- none
