---
type: eval
title: 'Eval: handoffs-list'
description: 'Definition of done for handoffs-list: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:36:34+00:00'
slug: handoffs-list
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 1c3c9d2a638ca8725df99117fab6e8d189ae5274f58cde6a438350f78c766068
  at: '2026-10-15T10:36:34+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl handoffs lists live handoffs newest first by generated.at, ties broken by file name.
  Fails when: the order differs from generated.at descending, or a tie is not ordered by file name
- r2: Handoffs past stale_after are left out; one with no stale_after is listed as live; index.md is never listed.
  Fails when: an expired handoff is listed, a handoff without stale_after is left out, or index.md appears
- r3: --json prints each entry with id, path, title, description and date, and [] when there is no handoffs folder.
  Fails when: an entry lacks any of the five keys, or the empty case is not []
- r4: Without .okf/handoffs/ the text output says there are none and exits 0.
  Fails when: the command exits nonzero or prints nothing
