---
type: plan
title: 'Plan: hermes-workflows'
description: kmctl's own repository answers /hermes comments and triages new issues with Hermes, with a triage comment under 200 tokens.
tags:
- plan
generated:
  by: process:loopctl/2.2.2.dev82+g0ed6ce5f1.d20261019
  at: '2026-10-20T08:26:09+00:00'
slug: hermes-workflows
epic: null
depends_on: []
priority: null
schema_version: '2.0'
---

# hermes-workflows

Relayed from: none

## Intent

kmctl's own repository gets the two Hermes workflows from the operator's
workspace repo: `new:.github/workflows/hermes-interactive.yaml`, which
answers a member's `/hermes` comment on an issue or pull request, and
`new:.github/workflows/hermes-issue-triage.yaml`, which comments on and
labels each new issue (or on a member's `/triage`). They come with their
system prompts, `new:.github/prompts/interactive-system.md` and
`new:.github/prompts/issue-triage-system.md`, and the okf skill the agent
loads, `new:.github/skills/okf/SKILL.md` with its references. Not the starter: the operator
chose kmctl's repository only.

The operator chose to keep the `JasperHG90/toiminnot` Hermes actions as
they are rather than port to `action/agent.py`; ADR 0017 rejected Hermes
for the audit only. The trigger is `/hermes`, never `@hermes`, which
mentions a GitHub account outside this repository.

The triage comment stays under 200 tokens. Measured over the workspace
repo (JasperHG90/loop-engineering-harness), the one triage comment Hermes
has posted there (issue 6) ran to 8467 characters, about 2100 tokens, so the
cap fires on 1 of 1. The Hermes action has no output
limit, so the prompt asks for a short form (summary, type and priority,
affected files, next step) and the apply step, moved from inline Python to
`new:scripts/hermes_triage.py` so tests can run it, cuts a longer comment at
a line break within 800 characters (about 200 tokens) and keeps the label
allowlist. The area labels match kmctl's top-level layout. A short ADR
records why kmctl runs Hermes here beside `action/agent.py`.

Outcome: `just test` passes with tests that pin both workflows to commit
SHAs, require `/hermes` and no `@hermes`, and show `scripts/hermes_triage.py`
cuts a 2000-character response to at most 800 characters while applying
only allowed labels.

## Problems

- P1: kmctl's repository has no agent that answers questions on issues and pull requests or triages new issues.
- P2: A Hermes triage comment can run to thousands of words, too long to read on every issue.

## Goals

- G1: Members get answers and triage on kmctl's own issues and pull requests without leaving GitHub.

## Outcomes

### O1: /hermes answers a member's comment on an issue or pull request
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:.github/workflows/hermes-interactive.yaml`, `new:.github/prompts/interactive-system.md`, `new:.github/skills/okf/SKILL.md`, `new:.github/skills/okf/references/SPEC.md`, `new:.github/skills/okf/references/APACHE-2.0.txt`
- checked by: tests/scripts/test_workflows.py checks the trigger, the member gate, the trusted checkout and SHA pins
- seen by: operator

### O2: New issues get a triage comment under 200 tokens and allowed labels
- kind: behaviour
- goal: G1
- fixes: P2
- needs: O1
- touches: `new:.github/workflows/hermes-issue-triage.yaml`, `new:.github/prompts/issue-triage-system.md`, `new:scripts/hermes_triage.py`
- checked by: tests/scripts/test_hermes_triage.py runs the script on long and labelled responses
- seen by: operator

### O3: An ADR records why kmctl's repository runs Hermes beside action/agent.py
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `new:.okf/decisions/0035-kmctl-s-repository-answers-and-triages-with-hermes.md`, `.okf/decisions/index.md`
- checked by: the okf-validate and kmctl-check hooks
- seen by: nobody

## Could invalidate this plan

- The copied okf skill under `.github/skills/` trips the repository's hooks (kmctl check, strict OKF validation, ruff) on files kmctl does not own, so the copy cannot be committed as is. Settled: every hook passed on the copy (spike:hermes-workflows/2).
