---
type: eval
title: 'Eval: ci-audit-hardening'
description: 'Definition of done for ci-audit-hardening: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T13:18:34+00:00'
slug: ci-audit-hardening
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: dfebe21feefe4b1fd2dcd052f885f4d928a5d24a39afed1e434685a1c6a8a203
  at: '2026-10-15T13:18:34+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The GitHub token reaches gh but not claude or its tools (f3).
  Fails when: the stub claude's recorded environment holds GH_TOKEN, GITHUB_TOKEN or the action's token variable, or the stub gh's does not hold GH_TOKEN, or action.yml sets GH_TOKEN for the audit step
- r2: A failed issue lookup fails the step and opens no issue (f4).
  Fails when: with a stub gh whose issue list exits nonzero, the script exits 0, or gh is called with issue create or issue edit
- r3: The audit path still writes the summary and the issue as before.
  Fails when: any other test in tests/test_ci_audit.py or tests/test_action.py fails
