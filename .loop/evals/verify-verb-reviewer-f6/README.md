---
type: eval
title: 'Eval: verify-verb-reviewer-f6'
description: 'Definition of done for verify-verb-reviewer-f6: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:49:00+00:00'
slug: verify-verb-reviewer-f6
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 32c5cedc7050a7f67f6dff8551237c5be04b504a494b735dd34f7d75ff306e6b
  at: '2026-10-18T21:49:00+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: When docs/ or .okf/ is a symlink to a folder outside the repository, kmctl verify on a page kmctl review due lists there writes its entry and names the page by its path inside the repository (as review due does), instead of raising ValueError.
  Fails when: verify raises, writes nothing, or names the page by a path outside the repository
- r2: The full suite and every tier pass.
  Fails when: any test fails
