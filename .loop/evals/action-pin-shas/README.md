---
type: eval
title: 'Eval: action-pin-shas'
description: 'Definition of done for action-pin-shas: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:32:31+00:00'
slug: action-pin-shas
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 483d6b0b274303675a408755317bf250b84a67ee94183acfed02afb5e26985f3
  at: '2026-10-19T14:32:31+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Every uses: line in action.yml pins a 40-character commit SHA followed by a # vX.Y.Z comment.
  Fails when: any uses: line in action.yml has a tag or branch ref, or no version comment
- r2: Every uses: line in .github/workflows/knowledge-audit.yml pins a 40-character commit SHA followed by a # vX.Y.Z comment.
  Fails when: any uses: line in knowledge-audit.yml has a tag or branch ref, or no version comment
- r3 (judgment): Each pinned SHA is the commit of the release its comment names, and the same action runs at one version across action.yml and the repo's workflows.
  Fails when: a SHA does not match its tag upstream, or one action is pinned at two versions
