---
type: eval
title: 'Eval: decision-supersede'
description: 'Definition of done for decision-supersede: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:52:40+00:00'
slug: decision-supersede
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 308f2223c0fddd790529acdabddc541bee988222301eb38b8dc39e39a99a2c59
  at: '2026-10-15T10:52:40+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl decision supersede OLD --by NEW sets the old record's status to deprecated and leaves its body and decision_status as they were.
  Fails when: status is not deprecated, decision_status changed, or any line of the old body before the appended section changed
- r2: The old record gets an appended dated Correction section linking the new record, and the new record links back.
  Fails when: either link is missing or the section is not dated
- r3: The decisions index marks the old entry as superseded by the new ADR and keeps its link.
  Fails when: the old entry lacks the superseded note or loses its link
- r4: A dated log line names both concept ids, and the bundle passes the pinned okf validator in strict mode.
  Fails when: log.md has no new line naming both ids, or the strict validator exits nonzero
- r5: It refuses, writing nothing, when either record does not exist or OLD is already deprecated.
  Fails when: any file changes, or the command exits 0, in any of the three cases
