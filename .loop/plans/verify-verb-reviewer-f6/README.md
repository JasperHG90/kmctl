---
type: plan
title: 'Plan: verify-verb-reviewer-f6'
description: Deferred hardening from verify-verb, reviewer finding f6 in review round 3.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.2.1.dev16+g27435b040.d20261017
  at: '2026-10-17T21:57:15+00:00'
slug: verify-verb-reviewer-f6
status: draft
epic: knowledge
depends_on: []
priority: null
---

# verify-verb-reviewer-f6

Relayed from: verify-verb, reviewer finding f6 in review round 3

## Intent

when docs/ (or .okf/) is a symlink to a folder outside the repository, verify raises ValueError at the rel computation instead of refusing or writing, though kmctl review due lists those pages at src/kmctl/verify.py:166.

## Could invalidate this plan

- none
