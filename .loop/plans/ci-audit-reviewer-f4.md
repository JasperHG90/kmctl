---
type: plan
title: 'Plan: ci-audit-reviewer-f4'
description: Deferred hardening from ci-audit, reviewer finding f4 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T13:09:48+00:00'
slug: ci-audit-reviewer-f4
status: draft
epic: ci
depends_on: []
priority: null
---

# ci-audit-reviewer-f4

Relayed from: ci-audit, reviewer finding f4 in review round 1

## Intent

Without pipefail, a failed `gh issue list` (rate limit, network) feeds empty input to the python filter, `number` comes back empty, and the script opens a second "Knowledge audit" issue instead of failing. at action/knowledge-audit.sh:71.

## Could invalidate this plan

- none
