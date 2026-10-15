---
type: eval
title: 'Eval: prototype-check'
description: 'Definition of done for prototype-check: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:53:55+00:00'
slug: prototype-check
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 155f2a69e044c967558a7e30113976d47742a202afb6ebc5aba38a4e3c46c344
  at: '2026-10-15T10:53:55+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl check passes when every folder directly under .okf/prototypes/ has a README.md.
  Fails when: kmctl check exits nonzero or reports a prototype finding on that fixture
- r2: A prototype whose nested folder has no README.md still passes.
  Fails when: kmctl check reports a prototype finding for a folder below a prototype
- r3: kmctl check fails and names the folder when a prototype has no README.md.
  Fails when: kmctl check exits 0, or the finding does not name the folder under check name prototype
