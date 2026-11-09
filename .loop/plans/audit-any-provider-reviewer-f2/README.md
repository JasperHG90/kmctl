---
type: plan
title: 'Plan: audit-any-provider-reviewer-f2'
description: Deferred hardening from audit-any-provider, reviewer finding f2 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T15:18:19+00:00'
slug: audit-any-provider-reviewer-f2
status: draft
epic: ci
depends_on: []
priority: null
---

# audit-any-provider-reviewer-f2

Relayed from: audit-any-provider, reviewer finding f2 in review round 1

## Intent

The whole prompt (skills, auditor text and the due list) goes to hermes as one argv string after -z. Linux caps one argument at 128 KiB (MAX_ARG_STRLEN), so a due list of roughly 800 or more concepts makes exec fail with E2BIG; the run then fails with "hermes exited 126" instead of a message that says why. The old script sent the prompt on stdin, so this ceiling is new. at action/knowledge-audit.sh:185.

## Could invalidate this plan

- none
