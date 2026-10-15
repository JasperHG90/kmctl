---
type: eval
title: 'Eval: new-doc-verb'
description: 'Definition of done for new-doc-verb: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T11:01:31+00:00'
slug: new-doc-verb
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 0251f9b8f86d9ad22a3663defcba6f72850b2701bf01da1f72e9ec4100db7cd9
  at: '2026-10-15T11:01:31+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl new doc TYPE TITLE creates the page in docs/TYPE/ with its title and that type's skeleton, for each of the four Diataxis types.
  Fails when: for any type the page is missing, is in the wrong folder, or lacks the title or skeleton headings
- r2: The new page is added to docs/README.md and kmctl check passes afterwards.
  Fails when: docs/README.md has no entry linking the page, or kmctl check exits nonzero
- r3: It refuses when docs/README.md is missing and names kmctl init.
  Fails when: it writes anything, exits 0, or the message does not name kmctl init
- r4: It never overwrites an existing page.
  Fails when: an existing page's content changes, or the command exits 0
