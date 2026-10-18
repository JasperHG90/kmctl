---
type: eval
title: 'Eval: apm-distribution-reviewer-f1'
description: 'Definition of done for apm-distribution-reviewer-f1: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:48:58+00:00'
slug: apm-distribution-reviewer-f1
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 1f97ac6c3986baeeda4d1c279001ed7d91bc464e79a0d78add36adbd289d1a31
  at: '2026-10-18T21:48:58+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: release-tag.yml reads the before commit's version from apm/apm.yml alone (a release.py subcommand or flag that does not require the root apm.yml to agree), so a before commit whose root apm.yml is missing or differs still gives its version, and compare can report lowered; only a before commit with no readable apm/apm.yml version gives an empty OLD.
  Fails when: the before read still uses `current || true`, a before commit with a differing root apm.yml gives an empty OLD, or a lowered version on such a commit is not refused
- r2: The full suite and every tier pass.
  Fails when: any test fails
