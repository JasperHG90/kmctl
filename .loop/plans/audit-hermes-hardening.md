---
type: plan
title: 'Plan: audit-hermes-hardening'
description: "The Hermes audit runs once per batch of at most ten concepts, so no prompt reaches Linux's 128 KiB argument limit, and it clears HERMES_MANAGED_DIR so no managed config overrides its own (audit-any-provider review findings f2 and f3)."
slug: audit-hermes-hardening
epic: ci
depends_on: [audit-any-provider]
priority: 9
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T15:56:14+00:00'
---

# audit-hermes-hardening

Relayed from: audit-any-provider, reviewer findings f2 and f3 in review round 1 (stubs audit-any-provider-reviewer-f2 and audit-any-provider-reviewer-f3)

## Intent

Two gaps in `action/knowledge-audit.sh`, both found by audit-any-provider's review:

- f2: the whole prompt goes to `hermes -z` as one argument. Linux caps one argument at 128 KiB, so a due list of roughly 800 or more concepts fails with "hermes exited 126" and no reason. The audit skill already works in batches of at most ten, so the script does the same: it groups the due concepts by kind (architecture, decisions, practices), splits each kind into batches of at most ten, and runs Hermes once per batch with the auditor text and that kind's review skill only. It pulls the findings block out of each run and passes the merged list to `audit-report.py` as one block, so that script's contract does not change. A batch that gives no usable findings fails the step and names the batch, as one run does today.
- Time: `KMCTL_AUDIT_TIMEOUT` (30 minutes by default) stays one budget for the whole audit, not per batch. Each run gets `timeout` with the time left; when the budget runs out the step fails, naming the batches it did not finish, before the workflow's `timeout-minutes: 40` would kill it silently. So `action.yml`, the workflow comment and the how-to's "stops Hermes after 30 minutes" stay true; the how-to adds one line that the limit covers all batches together (round 1 plan review).
- f3: Hermes 0.19.0 reads `HERMES_MANAGED_DIR`, a managed config and `.env` applied last, which would beat the config the script writes. The script clears it with the other Hermes variables.

Measured: the prompt today is about 9 KB plus about 150 bytes per due concept, so 1 of 1 runs over roughly 800 due concepts fails; with batches of ten the largest prompt stays near 11 KB. The unset list holds 4 of the 5 Hermes variables that change where config comes from.

Done when a test with a stub hermes and 25 due concepts (12 architecture, 8 decisions, 5 practices) shows 4 runs (two architecture, one decisions, one practices), each with at most ten concepts of one kind and only that kind's review skill, every prompt under 64 KiB, and the summary holding all 25 findings; a test with a stub hermes that sleeps shows the whole audit stops when the total budget runs out, naming the unfinished batches; a test shows a batch with no findings fails the step naming the batch and posts no body; a test shows `HERMES_MANAGED_DIR` set in the caller's environment does not reach hermes; and the other audit tests pass.

## Could invalidate this plan

- none (the time budget across batches, the one risk round 1 named, is settled in the intent above)
