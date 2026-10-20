---
type: plan
title: 'Plan: hermes-workflows-reviewer-f2'
description: Deferred hardening from hermes-workflows, reviewer finding f2 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.2.2.dev82+g0ed6ce5f1.d20261019
  at: '2026-10-20T08:55:42+00:00'
slug: hermes-workflows-reviewer-f2
epic: null
depends_on: []
priority: null
schema_version: '2.0'
---

# hermes-workflows-reviewer-f2

Relayed from: hermes-workflows, reviewer finding f2 in review round 1

## Intent

The Apply triage step in `.github/workflows/hermes-issue-triage.yaml` puts
`steps.hermes.outputs.response_file` straight into its shell line. Pass it
through `env` as `RESPONSE_FILE` and quote `"$RESPONSE_FILE"`, as the source
workflow did and GitHub's hardening guide asks, so no step output is
expanded into a script. Outcome: a test fails when any `run:` in the Hermes
workflows holds `${{ steps.`.

## Problems

- P1: A step output is expanded into the Apply triage shell line instead of read from the environment.

## Goals

- G1: The Hermes workflows run no shell line built from step outputs.

## Outcomes

### O1: Apply triage reads the response file path from RESPONSE_FILE
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `.github/workflows/hermes-issue-triage.yaml`, `tests/scripts/test_workflows.py`
- checked by: tests/scripts/test_workflows.py checks no run: in either Hermes workflow expands a step output
- seen by: nobody

## Could invalidate this plan

- none
