---
type: eval
title: 'Eval: ci-per-package'
description: 'Definition of done for ci-per-package: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:47:12+00:00'
slug: ci-per-package
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 014a5247594d57d741f63be1d90c8aa7dbb9ea48c473a80c24c5cd2c6833935f
  at: '2026-11-14T17:47:12+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: ci.yml is named CI and runs prek, then knowledge, then the kmctl, kmaudit, repo and starter jobs, each test job running pytest in its own directory.
  Fails when: the name is not CI, a job is missing, the needs order differs, or a test job runs the wrong directory
- r2: A tests job needs kmctl, kmaudit and repo, runs if: always(), and fails unless every one succeeded; prek, knowledge and tests carry no name: so the required checks keep their names.
  Fails when: the tests job is missing, lacks always(), passes when one job failed or was skipped, or a required job has a name:
- r3: Every test the loop's tests gate collects sits under exactly one CI test job's directory, each job directory collects at least one test, and both packages appear.
  Fails when: a collected test is in no job or in two, a job collects nothing, or a package is missing
