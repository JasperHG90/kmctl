---
type: plan
title: 'Plan: link-check-reviewer-f4'
description: Deferred hardening from link-check, reviewer finding f4 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T11:03:01+00:00'
slug: link-check-reviewer-f4
status: draft
epic: cli
depends_on: []
priority: null
---

# link-check-reviewer-f4

Relayed from: link-check, reviewer finding f4 in review round 1

## Intent

Links that GitHub renders fine are reported as broken: percent-encoded paths (my%20page.md) and query strings (file.md?plain=1). Other links are skipped without notice: titles in single quotes, <angle brackets> with spaces, and reference-style [x][ref] definitions. at src/kmctl/checks.py:28.

## Could invalidate this plan

- none
