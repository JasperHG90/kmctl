---
type: eval
title: 'Eval: audit-hermes-hardening'
description: 'Definition of done for audit-hermes-hardening: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T15:56:26+00:00'
slug: audit-hermes-hardening
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 10e8f3520c47361768cabd1c534f4cd092f1a46cd32032806052b1c22081f6c7
  at: '2026-10-15T15:56:26+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The audit runs Hermes once per batch of at most ten due concepts, each prompt well under the argument limit, and merges every batch's findings (f2).
  Fails when: with a stub hermes and 25 in-scope due concepts, hermes is not called 3 times, a call carries more than ten concepts or a prompt of 64 KiB or more, or the summary and body do not hold all 25 findings
- r2: A batch whose run gives no usable findings fails the step, naming the batch, and posts no body.
  Fails when: with a stub hermes that answers the second of three batches with no findings block, the script exits 0, the message does not name the batch, or a body is written under RUNNER_TEMP
- r3: HERMES_MANAGED_DIR set in the caller's environment does not reach hermes (f3).
  Fails when: the stub hermes's recorded environment holds HERMES_MANAGED_DIR
- r4: The other audit and plugin tests still pass.
  Fails when: any test in tests/test_ci_audit.py, tests/test_hermes_plugin.py or tests/test_action.py fails
