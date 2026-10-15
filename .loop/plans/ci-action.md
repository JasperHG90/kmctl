---
type: plan
title: 'Plan: ci-action'
description: "A reusable GitHub Action that runs kmctl check and review due on every PR, and an opt-in LLM audit that reports only (ADR 0005)."
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

Adds `new:action.yml`, a composite action, with two modes:

- `checks` (default): installs kmctl, runs `kmctl check` and `kmctl review due --json`, writes the result to the job summary, and fails only on `kmctl check`.
- `audit` (opt-in, needs an Anthropic API key secret): runs the audit agent through Claude Code in CI and posts its findings as a comment or job summary. It never pushes (I2).

This repository uses the action on itself in a workflow.

Done when the workflow runs `checks` green on a pull request here.

## Could invalidate this plan

- none
