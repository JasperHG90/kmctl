---
type: plan
title: 'Plan: ci-audit'
description: "The GitHub Action gains an opt-in audit mode that runs the audit agent through Claude Code in CI and reports its findings, never pushing (ADR 0005, I2)."
slug: ci-audit
epic: ci
depends_on: [ci-action, audit-agent-and-skills]
priority: 11
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:07:39+00:00'
---

# ci-audit

Relayed from: none

## Intent

Adds a `mode: audit` input to `action.yml`. It needs an Anthropic API key secret, runs the audit agent through Claude Code in CI, and posts its findings as a pull request comment or job summary. It never pushes and never writes knowledge (I2). Without the input the action behaves as before.

Done when a test run on a fixture repository posts findings and the job's token has no write permission to contents.

## Could invalidate this plan

- none
