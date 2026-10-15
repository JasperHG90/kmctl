---
type: plan
title: 'Plan: ci-audit-reviewer-f3'
description: Deferred hardening from ci-audit, reviewer finding f3 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T13:09:48+00:00'
slug: ci-audit-reviewer-f3
status: draft
epic: ci
depends_on: []
priority: null
---

# ci-audit-reviewer-f3

Relayed from: ci-audit, reviewer finding f3 in review round 1

## Intent

GH_TOKEN is set for the whole audit step, so the claude process and its tools inherit it although only gh needs it. The Read tool can read /proc/self/environ, and the summary text goes into an issue. Set GH_TOKEN only for the gh calls. at action.yml:56.

## Could invalidate this plan

- none
