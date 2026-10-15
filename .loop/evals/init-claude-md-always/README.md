---
type: eval
title: 'Eval: init-claude-md-always'
description: 'Definition of done for init-claude-md-always: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:32:13+00:00'
slug: init-claude-md-always
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 3d954475ad4ca4033d9f5ca3b540f7f369086309fe49ca06419b8365db816e61
  at: '2026-10-15T16:32:13+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init writes CLAUDE.md with the kmctl block whenever it is missing, and adds the block to AGENTS.md when that exists.
  Fails when: in a repository with only AGENTS.md, after init CLAUDE.md is missing or lacks the block, or AGENTS.md lacks the block or loses any of its text
- r2: A CLAUDE.md or AGENTS.md symlink that is dangling or points outside the repository is left alone with a warning naming the link and its target.
  Fails when: init creates or changes the target of a dangling link or of a link outside the repository, or gives no warning naming the link
- r3: The other init tests still pass.
  Fails when: any test in tests/test_init.py fails
