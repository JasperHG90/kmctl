---
type: eval
title: 'Eval: ci-per-package'
description: 'Definition of done for ci-per-package: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:50:58+00:00'
slug: ci-per-package
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 4f563484fdb94c814d1cceb39a238e62a30ddd914a2e085c52fc75061bfcc113
  at: '2026-11-14T17:50:58+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: ci.yml is named CI and runs prek, then knowledge, then the kmctl, kmaudit, repo and starter jobs, each test job running pytest with markers not integration in its own directory (packages/kmctl/tests, packages/kmaudit/tests, tests); the kmctl job installs just before pytest, and the starter job runs packages/kmctl/tests/test_starter.py -m integration.
  Fails when: the name is not CI, a job is missing, the needs order differs, a test job runs the wrong directory or drops the not integration marker, the kmctl job runs pytest before installing just, or the starter job runs any other path
- r2: A tests job needs kmctl, kmaudit and repo, runs if: always(), and fails unless every one succeeded; prek, knowledge and tests carry no name:, so the ruleset's required checks prek, knowledge and tests keep reporting.
  Fails when: the tests job is missing, lacks always(), passes when one of the three failed or was skipped, or prek, knowledge or tests has a name:
- r3: Collecting each CI test job's directory on its own gives counts that sum to what the loop's tests gate (uv run pytest at the root) collects; the per-job test ids do not overlap and together equal the gate's ids; each job collects at least one test, and both packages/kmctl and packages/kmaudit appear.
  Fails when: the per-job counts do not sum to the gate's count, a test id is in two jobs or in none, a job collects nothing, or a package is missing
