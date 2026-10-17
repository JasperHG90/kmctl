---
type: eval
title: 'Eval: ci-toiminnot'
description: 'Definition of done for ci-toiminnot: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T18:05:01+00:00'
slug: ci-toiminnot
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 542df600807edfb95caf0a7e0b5556885cd25f19dc8620115072e9ab18768d72
  at: '2026-10-17T18:05:01+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: ci.yml's prek job puts uv on PATH, then runs prek at the justfile's version through toiminnot's pre_commit action (which runs prek in v1.3.0) on Python 3.12
  Fails when: the prek job has no setup-uv step before a JasperHG90/toiminnot/actions/pre_commit step, or that step's prek_version differs from the justfile's prek@ version, or its python_version is not 3.12
- r2: ci.yml's tests job runs toiminnot's pytest action on tests/, leaving out the integration tier, on Python 3.12
  Fails when: the tests job has no JasperHG90/toiminnot/actions/pytest step, or its inputs are not directory tests, markers 'not integration' and python_version 3.12
- r3: every action in ci.yml, toiminnot's included, is pinned by commit SHA, and the setup-uv steps ci.yml writes have their cache off
  Fails when: a uses: other than ./ is not owner/repo[/path]@<40-character SHA>, or a setup-uv step in ci.yml lacks enable-cache: false
- r4: the triggers, the knowledge job and the how-to's quoted workflows still hold
  Fails when: any of test_ci.py's trigger, knowledge or quoted tests fails
