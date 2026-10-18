---
type: eval
title: 'Eval: verify-verb-reviewer-f4'
description: 'Definition of done for verify-verb-reviewer-f4: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:48:59+00:00'
slug: verify-verb-reviewer-f4
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 7ac549acfd2f8db10c8f7fca703ea74a400d3f6760cb84a15dcc6cabe8132111
  at: '2026-10-18T21:48:59+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl verify adds its entry when the verified line carries a trailing YAML comment: `verified:  # checks` over a block list gets the entry appended to that list, and `verified: []  # none` becomes a list with the one entry; the comment is kept and the front matter still parses to the same entries plus the new one.
  Fails when: verify refuses either form, drops or corrupts the comment or another entry, or the result does not parse
- r2: The full suite and every tier pass.
  Fails when: any test fails
