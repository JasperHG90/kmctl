---
type: eval
title: 'Eval: first-decision-detect'
description: 'Definition of done for first-decision-detect: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:32:29+00:00'
slug: first-decision-detect
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 20712bbfab4fcc1a2dbcbdb080705ceb72b1d892a4cb9c68bd3e39dbf3a80696
  at: '2026-10-19T14:32:29+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init over a bundle whose .okf/decisions/ holds records with other titles (a copy of this repository's .okf/) writes no decision record and leaves every file under .okf/ byte for byte.
  Fails when: any new file appears under .okf/decisions/, or any file under .okf/ changes
- r2: kmctl init over a .okf/decisions/ holding only index.md writes the first decision as 0001.
  Fails when: no 0001 record with the first decision's title is written
- r3: A decision record whose front matter does not parse still counts as a record, so init writes no first decision beside it.
  Fails when: init writes a first decision when the only record has broken front matter
- r4: The existing init tests and the rest of the suite pass under the new rule.
  Fails when: any test in tests/test_init.py fails
- r5 (judgment): ADR 0011 carries a dated Correction stating the empty-folder rule and citing issue #26; the scaffold docstrings, the kmctl init epilog and docs/reference/commands.md state the new rule and none still states the title rule.
  Fails when: the Correction is missing, or any of those places still describes matching the first decision's title
