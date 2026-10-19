---
type: eval
title: 'Eval: release-cache-off'
description: 'Definition of done for release-cache-off: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-19T01:07:56+00:00'
slug: release-cache-off
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 823048fdc50576dcbd487052414368e458c959c547f0256f2a5965b9c0a54dfd
  at: '2026-10-19T01:07:56+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Every astral-sh/setup-uv step in .github/workflows/release.yml and .github/workflows/release-tag.yml sets enable-cache: false, so no workflow that tests, builds or publishes a release restores an Actions cache entry another job could have written.
  Fails when: any setup-uv step in either workflow omits enable-cache or sets it true
- r2: A decision record says why the release workflows run without the uv cache (the audit agent runs shell commands as the runner's user and could write cache entries on main, ADR 0017), as a Correction to ADR 0012 or ADR 0017.
  Fails when: neither ADR 0012 nor ADR 0017 carries a dated Correction naming the release workflows' cache
- r3: The full suite and every tier pass.
  Fails when: any test fails
