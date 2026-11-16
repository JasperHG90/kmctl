---
type: eval
title: 'Eval: decision-gaps-measure'
description: 'Definition of done for decision-gaps-measure: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T11:47:43+00:00'
slug: decision-gaps-measure
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 02db8c6af53d56d6109d7fce3667b4df97ed600824671bf51e650db9baddca0b
  at: '2026-11-16T11:47:43+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Rerunning the prototype's units and signals scripts over the fixed range reproduces the committed units and filter results, and the README's filter table (recall of hidden positives and share of units flagged, per threshold) equals what score.py prints from them.
  Fails when: the units or filter results differ from the committed ones, or a number in the README's filter table differs from score.py's output
- r2: The README's judge numbers (recall on hidden positives, missing-decision rate on the negative sample, precision of those claims from the committed labels, and cost and time per unit) equal what score.py prints from the committed judge results and labels, and every judged unit in the sample has a result and every judge claim on a negative a label.
  Fails when: a judged unit lacks a result, a claim lacks a label, or a judge number in the README differs from score.py's output
- r3: The prototype folder is a valid concept: its README has the prototype front matter, the prototypes index lists it, and kmctl check and strict OKF validation pass.
  Fails when: kmctl check or the frontmatter tests report a finding
