---
type: eval
title: 'Eval: audit-drift-followup'
description: 'Definition of done for audit-drift-followup: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-19T01:07:56+00:00'
slug: audit-drift-followup
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: f82d141c2149b258fcda9eca877cd4f8c31d1d356402885f6d2723831894d8f3
  at: '2026-10-19T01:07:56+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1 (judgment): Each mismatch the plan lists is checked against today's code: a real one is fixed (a dated Correction appended to a decision record, never a rewrite; a direct edit to an architecture page or a docs page), one already fixed or not real is left alone and named as such in the commit message; HOOK_DESCRIPTION's wording changes only if nothing matches on that text.
  Fails when: a listed mismatch that is still real is left unfixed, a decision record's earlier text is rewritten rather than corrected, or a docs or architecture claim the change makes is false
- r2: kmctl check passes, the bundle passes strict OKF validation, and the summary is not left behind the changed concepts.
  Fails when: kmctl check or strict validation fails, or kmctl review due lists the summary for the changed concepts
- r3: The full suite and every tier pass.
  Fails when: any test fails
