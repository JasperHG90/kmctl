---
type: eval
title: 'Eval: decision-gaps-measure'
description: 'Definition of done for decision-gaps-measure: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T11:52:25+00:00'
slug: decision-gaps-measure
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 7d968dac9701ae23b3992bf6b6ad1bdfa85ab68fda29b54d45adee38572de8c8
  at: '2026-11-16T11:52:25+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Rerunning the prototype's units and signals scripts over the fixed range reproduces the committed units and filter results, and the README's filter table (recall of hidden positives and share of units flagged, per threshold) equals what score.py prints from them.
  Fails when: the units or filter results differ from the committed ones, or a number in the README's filter table differs from score.py's output
- r2: The judge ran on every unit in the range from an empty folder with no tools or settings; the README's judge numbers (recall on counted positives with its 95% Wilson interval, record-only positives listed apart, the share of negatives called missing, the precision of those claims from the committed labels, cost and time per unit and for the range) and its build verdict against the bars in the plan (recall >= 70% with Wilson lower end >= 50%, precision >= 50%, range cost <= $10) equal what score.py prints from the committed judge results and labels; every unit has a judge result and every claim on a negative a label.
  Fails when: a unit lacks a judge result, a claim lacks a label, a judge number or the verdict in the README differs from score.py's output, or a record-only positive is counted in recall
- r3: The prototype folder is a valid concept: its README has the prototype front matter, the prototypes index lists it, and kmctl check and strict OKF validation pass.
  Fails when: kmctl check or the frontmatter tests report a finding
