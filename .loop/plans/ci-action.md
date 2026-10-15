---
type: plan
title: 'Plan: ci-action'
description: "A reusable GitHub Action that runs kmctl check and kmctl review due on every pull request, at no model cost (ADR 0005)."
slug: ci-action
epic: ci
depends_on: [knowledge-check, review-due]
priority: 10
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:23+00:00'
---

# ci-action

Relayed from: none

## Intent

Adds `new:action.yml`, a composite action that installs kmctl, runs `kmctl check` and `kmctl review due --json`, writes both to the job summary, and fails only on `kmctl check`. This repository uses it on itself in a workflow under .github/workflows/.

Done when the workflow runs green on a pull request here.

## Could invalidate this plan

- none
