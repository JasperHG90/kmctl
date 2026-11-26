---
type: plan
title: 'Plan: action-failure-points-to-summary'
description: A failed check in the Action points the job log at the run's summary page, with a link.
tags:
- plan
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T13:10:06+00:00'
slug: action-failure-points-to-summary
epic: null
depends_on: []
priority: null
schema_version: '2.0'
---

# action-failure-points-to-summary

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none
<!-- When this ticket carries a finding raised while building another ticket,
replace "none" with that ticket's slug and the finding, in one line (ADR 0001). -->

## Intent

When `kmctl check` or `kmctl review due` fails in the GitHub Action,
`action/knowledge-ci.sh` writes the reasons only to the job summary, so the
job log says just "Process completed with exit code 1" (dlx run 45802219402).
The script will print an `::error` line to the log that names the failed
command and says the reasons are on the run's summary page, with a link built
from `GITHUB_SERVER_URL`, `GITHUB_REPOSITORY`, `GITHUB_RUN_ID` and
`GITHUB_RUN_ATTEMPT`. It worked when a failing run's log carries that line
and link.

## Problems

- P1: A failed check in the Action logs only an exit code; the reasons sit in the job summary and nothing in the log says so.

## Goals

- G1: Someone reading a failed job's log learns which kmctl command failed and follows one link to the reasons.

## Outcomes

### O1: A failing check prints an error line with a link to the run's summary page
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `action/knowledge-ci.sh`, `packages/kmctl/tests/test_action.py`, `docs/how-to/install-the-plugin-and-the-ci-action.md`
- checked by: tests running the script with a failing kmctl check and a crashing kmctl review due, asserting the ::error line and the run URL on stdout, and none on a passing run
- seen by: operator

## Could invalidate this plan

- none
