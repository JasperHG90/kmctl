---
type: plan
title: 'Plan: audit-any-provider-reviewer-f3'
description: Deferred hardening from audit-any-provider, reviewer finding f3 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T15:18:19+00:00'
slug: audit-any-provider-reviewer-f3
status: draft
epic: ci
depends_on: []
priority: null
---

# audit-any-provider-reviewer-f3

Relayed from: audit-any-provider, reviewer finding f3 in review round 1

## Intent

The script unsets HERMES_PROFILE, HERMES_CONFIG, HERMES_ENV and HERMES_ENABLE_PROJECT_PLUGINS, but Hermes 0.19.0 also reads HERMES_MANAGED_DIR (hermes_cli/managed_scope.py), a managed config and .env applied last with override, which beats the config the script writes. It belongs in the same unset list. at action/knowledge-audit.sh:175.

## Could invalidate this plan

- none
