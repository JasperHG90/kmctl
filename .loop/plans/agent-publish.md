---
type: plan
title: 'Plan: agent-publish'
description: A publish command in action/agent.py that opens or updates one issue only when the report has a finding at or above a severity, and @-mentions the CODEOWNERS owners.
tags:
- plan
slug: agent-publish
status: draft
epic: null
depends_on:
- standalone-agent
priority: null
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:59:56+00:00'
---

# agent-publish

Relayed from: none

## Intent

Add `publish` to the standalone agent script (`action/agent.py`, from the
`standalone-agent` ticket). It reads `report.json` and, run in its own step
with the only GitHub token in the job, opens or updates one issue only when a
finding is at or above `--min-severity`. The issue @-mentions the owners of
`*` in CODEOWNERS, or whoever `--mention` names instead. It replaces
`action/knowledge-audit-issue.sh` in `action.yml` and
`.github/workflows/knowledge-audit.yml`.

The outcome: a report with no finding at the threshold opens no issue, and
one with such a finding opens or updates the issue with the owners mentioned.

## Could invalidate this plan

- none
