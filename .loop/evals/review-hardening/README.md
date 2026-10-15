---
type: eval
title: 'Eval: review-hardening'
description: 'Definition of done for review-hardening: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev77+gbd4712cf8.d20261015
  at: '2026-10-15T11:58:02+00:00'
slug: review-hardening
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: a3b5426f3042f17d1ff515d79a5745dd508356dae7571ff2d35f50bfb6f45d46
  at: '2026-10-15T11:58:02+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init with a kept .okf/index.md that is not UTF-8 exits 0 and warns that the kept file is not UTF-8.
  Fails when: init raises, exits nonzero, or gives no not-UTF-8 warning
- r2: A handoff whose generated.at overflows the datetime range does not crash kmctl handoffs or kmctl review due.
  Fails when: either command exits nonzero or prints a traceback
- r3: Percent-encoded, ?query, angle-bracket and single-quote-titled targets resolve in both the index check and the link check.
  Fails when: any of these forms pointing at an existing page is reported, in docs/ pages or in docs/README.md entries
- r4: Reference-style definitions are checked by the link check, and the index check's entry format is unchanged.
  Fails when: a broken [ref]: path definition is not reported under check name link, or a reference-style list item counts as an index entry
- r5: The write-docs grader finds each run's type through eval_metadata.json's eval_id, for folder names evals.json does not hold, and reports a folder with no metadata or a mismatched prompt instead of grading it.
  Fails when: the grader raises, grades a folder without metadata, or grades a run whose metadata prompt differs from the eval's prompt
