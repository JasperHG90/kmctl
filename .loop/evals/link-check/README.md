---
type: eval
title: 'Eval: link-check'
description: 'Definition of done for link-check: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:59:05+00:00'
slug: link-check
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: fdefa0be765d4dbdeb5baf737236c950d864ad153602595293b0a2a3d08d2e9e
  at: '2026-10-15T10:59:05+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In docs/, a relative link resolves from the page's folder: a good one passes and a broken one fails with its file and line.
  Fails when: the good link is reported, or the broken one is not reported with file and line under check name link
- r2: In docs/, a link starting with / resolves from the repository root.
  Fails when: a / link to an existing repository file is reported, or one to a missing file is not
- r3: In .okf/, a relative link that leaves the bundle is checked.
  Fails when: a link like ../src/x.py to a missing file is not reported, or one to an existing file is
- r4: A broken link inside .okf/ is left to the okf validator and not reported.
  Fails when: kmctl check reports a broken in-bundle .okf/ link
- r5: URLs and anchors are not checked.
  Fails when: an http(s) link or a #anchor link is reported
