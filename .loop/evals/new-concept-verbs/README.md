---
type: eval
title: 'Eval: new-concept-verbs'
description: 'Definition of done for new-concept-verbs: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:45:38+00:00'
slug: new-concept-verbs
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: ef5709c130925754000b2a671f80d47aef95cb721d100947c909b9dacbfdcb99
  at: '2026-10-15T10:45:38+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl new KIND TITLE --description TEXT creates the concept for each of decision, practice, proposal, prototype and handoff, with its front matter and that kind's heading skeleton.
  Fails when: for any kind the file is missing, misnamed, lacks type, title, description, tags or generated, or lacks the skeleton headings
- r2: Decisions get the next four-digit number and handoffs get a stale_after date.
  Fails when: a new decision's number is not one more than the highest, or a handoff has no stale_after
- r3: The first concept in a section creates the section folder, its index.md and the root index link.
  Fails when: after the first concept, the section index or the root link is missing
- r4: Each new concept is indexed and logged, kmctl check passes, and the bundle passes the pinned okf validator in strict mode.
  Fails when: the section index has no entry, log.md has no line naming the id, kmctl check exits nonzero, or the strict validator exits nonzero
- r5: It refuses, writing nothing, when the file already exists, including two handoffs with the same title.
  Fails when: any file changes or the command exits 0
