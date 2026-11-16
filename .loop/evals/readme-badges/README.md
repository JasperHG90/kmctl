---
type: eval
title: 'Eval: readme-badges'
description: 'Definition of done for readme-badges: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T09:06:44+00:00'
slug: readme-badges
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 24ef7d1a3118f45936b18b1ece187be0eeaec22b682f4041fd32b5921a8ba17e
  at: '2026-11-16T09:06:44+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The root README and both package READMEs carry a CI badge for ci.yml on main, a licence badge and a Python badge; each package README and the root README's entry for each package carry a lifecycle badge and a release badge filtered to that package's tag family (v* for kmctl, kmaudit-v* for kmaudit).
  Fails when: a README lacks one of the badges, the CI badge names another workflow or branch, or a release badge does not filter to its own package's tags
- r2: kmaudit's lifecycle badge says beta and kmctl's stable; kmaudit's README, docs/reference/kmaudit-commands.md and the root README's kmaudit entry say kmaudit is beta; packages/kmaudit/pyproject.toml carries Development Status :: 4 - Beta and packages/kmctl/pyproject.toml Development Status :: 5 - Production/Stable; every earlier README test passes.
  Fails when: either lifecycle badge says the wrong state, one of the three texts does not say beta, a classifier is missing or wrong, or any test in test_readmes.py fails
