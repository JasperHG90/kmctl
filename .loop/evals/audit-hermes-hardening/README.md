---
type: eval
title: 'Eval: audit-hermes-hardening'
description: 'Definition of done for audit-hermes-hardening: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T15:58:00+00:00'
slug: audit-hermes-hardening
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 376d2af873061c74e62964c7e708790557d2bdd21a11ac8ec8fcb323df812262
  at: '2026-10-15T15:58:00+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The audit groups due concepts by kind, runs Hermes once per batch of at most ten concepts of one kind with only that kind's review skill, keeps every prompt well under the argument limit, and merges every batch's findings (f2).
  Fails when: with a stub hermes and 25 in-scope due concepts (12 architecture, 8 decisions, 5 practices), hermes is not called 4 times (2, 1 and 1 per kind), a call mixes kinds, carries more than ten concepts, holds another kind's review skill, or a prompt of 64 KiB or more, or the summary and body do not hold all 25 findings
- r2: A batch whose run gives no usable findings fails the step, naming the batch, and posts no body.
  Fails when: with a stub hermes that answers the second of three batches with no findings block, the script exits 0, the message does not name the batch, or a body is written under RUNNER_TEMP
- r3: HERMES_MANAGED_DIR set in the caller's environment does not reach hermes (f3).
  Fails when: the stub hermes's recorded environment holds HERMES_MANAGED_DIR
- r5: KMCTL_AUDIT_TIMEOUT is one budget for the whole audit: each batch gets the time left, and when it runs out the step fails naming the unfinished batches.
  Fails when: with a budget of a few seconds and a stub hermes that sleeps longer per batch, the audit runs past the budget plus a small margin, exits 0, does not name the unfinished batches, or writes a body
- r4: The other audit and plugin tests still pass.
  Fails when: any test in tests/test_ci_audit.py, tests/test_hermes_plugin.py or tests/test_action.py fails
