---
type: eval
title: 'Eval: review-due'
description: 'Definition of done for review-due: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:42:55+00:00'
slug: review-due
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 7b945372aa2d5e72105ab0acb75b22f79ac212a71c069d72507457d86195b3da
  at: '2026-10-15T10:42:55+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: A concept whose stale_after has passed is due with that reason.
  Fails when: the concept is not listed, or its reason is not stale_after
- r2: A concept with no verified entry is due with that reason.
  Fails when: the concept is not listed, or its reason is not unverified
- r3: A concept is due when a tracked source file changed in git after its last verified date, for bundle-root, concept-relative, repository-root and concept-id sources.
  Fails when: any of the four forms, changed after verification, is not reported, or is reported when unchanged
- r4: URLs are skipped, and a source that resolves to no tracked file is listed as a source-not-resolved notice, not as a due reason.
  Fails when: a URL is reported, or a free-text source makes the concept due
- r5: Handoffs are left out of the concept checks, and an expired handoff is listed once, under expired handoffs.
  Fails when: a live handoff is due for lacking verified, or an expired one appears twice
- r6: In a shallow clone the history reason is skipped and the output says so.
  Fails when: a shallow clone reports a source-changed reason, or the output does not say the reason was skipped
- r7: It exits 0 whether or not anything is due, and --json prints the same result as one object.
  Fails when: the exit code is nonzero when concepts are due, or --json output is not one object with due, notices and expired handoffs
