---
type: eval
title: 'Eval: repo-ci'
description: 'Definition of done for repo-ci: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:40:47+00:00'
slug: repo-ci
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 889b52d095015adcd146aecd1eef831e39990bc6a3edf51cdb816e984de32e39
  at: '2026-10-17T17:40:47+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: ci.yml runs on every pull request and on every push to main
  Fails when: ci.yml is missing, or its on: block lacks pull_request or a push trigger limited to main
- r2: ci.yml's knowledge job runs kmctl's own check with uses: ./ after a full-history checkout
  Fails when: no job has a uses: ./ step, or its checkout lacks fetch-depth: 0
- r3: ci.yml's prek job runs uvx prek at the version justfile pins, on all files
  Fails when: no job runs uvx prek@<the justfile's version> run --all-files
- r4: ci.yml's tests job runs the default test suite with uv run pytest
  Fails when: no job runs uv run pytest, or it passes a -m that changes the default tier
- r5: every action in ci.yml is pinned by commit SHA and setup-uv runs with its cache off
  Fails when: a uses: other than ./ is not a 40-character SHA, or a setup-uv step lacks enable-cache: false
- r6: knowledge.yml is gone, so kmctl check runs once per pull request
  Fails when: .github/workflows/knowledge.yml exists
- r7: the install how-to quotes only workflows this repository ships, naming ci.yml's knowledge job instead of knowledge.yml
  Fails when: a .github/workflows/ path in the how-to's 'quoted from' note or its step 4 'shipped' sentence does not exist in the repository
