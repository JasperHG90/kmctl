---
type: plan
title: 'Plan: apm-distribution-reviewer-f1'
description: Deferred hardening from apm-distribution, reviewer finding f1 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T11:05:39+00:00'
slug: apm-distribution-reviewer-f1
status: draft
epic: plugin
depends_on: []
priority: null
---

# apm-distribution-reviewer-f1

Relayed from: apm-distribution, reviewer finding f1 in review round 1

## Intent

release-tag.yml reads the before commit with `release.py current ... || true`, and current now also refuses on a missing or differing apm.yml, so any such before commit gives an empty OLD, which compare treats as raised and so skips the lowered-version guard. It does not break 0.2.0 (main's before commit will hold both apm.yml files at 0.1.0), but the before read only needs the manifest's version. at .github/workflows/release-tag.yml:55.

## Could invalidate this plan

- none
