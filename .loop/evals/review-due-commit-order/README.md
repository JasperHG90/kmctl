---
type: eval
title: 'Eval: review-due-commit-order'
description: 'Definition of done for review-due-commit-order: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T15:09:39+00:00'
slug: review-due-commit-order
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: ad4868ccf6b9919b2bbb47196a8079ad62ad1ed2c547d95ff5c634809a930643
  at: '2026-10-19T15:09:39+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: A concept verified on a branch is not due after the branch lands by squash merge, rebase merge or merge commit when nothing changed after the verification.
  Fails when: review due lists the concept after any of the three landings
- r2: A concept is due 'source changed' when a commit after its verification commit changes one of its sources.
  Fails when: the concept is not listed with source changed naming that source
- r3: A concept is due 'edited after verification' when a commit after its verification commit changes its body or a front matter field other than verified and stale_after.
  Fails when: the concept is not listed with that reason, for a body edit or for a description edit
- r4: A commit that only adds a verified entry, with or without --stale-after, leaves the concept off the list; an uncommitted verified entry counts nothing as changed after it.
  Fails when: the concept is listed after a verify-only commit, with or without stale_after
- r5: A docs page follows the same two rules, and one without verified uses its own last commit as the baseline, by commit not date.
  Fails when: a docs page gets a different answer than a concept in the same case, or the unverified baseline compares dates
- r6: The batched history walk picks the same verification commit as a per-file git log, including across a merge and a rename.
  Fails when: the batched and per-file walks pick different commits for any file in the test repository
- r7: The existing review due tests still pass.
  Fails when: any test in tests/test_review_due.py fails
- r8 (judgment): A new decision records that review due decides by commit order and names the new reason; ADR 0006 and ADR 0023 carry dated corrections pointing to it; the module docstring, the review due help, docs/reference/commands.md and the docs-layout rule say the same.
  Fails when: the decision or a correction is missing, or any of those surfaces still describes comparing dates
