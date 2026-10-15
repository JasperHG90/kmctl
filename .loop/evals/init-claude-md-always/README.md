---
type: eval
title: 'Eval: init-claude-md-always'
description: 'Definition of done for init-claude-md-always: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:36:44+00:00'
slug: init-claude-md-always
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: ea4d2806ddfc7c57710f47cdc20192ca6020c6b52fc7c4c4ee6a45ac92489061
  at: '2026-10-15T16:36:44+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: With AGENTS.md and no CLAUDE.md, kmctl init adds the block to AGENTS.md and writes a CLAUDE.md holding only @AGENTS.md; with neither, it writes CLAUDE.md with the block.
  Fails when: in a repository with only AGENTS.md, after init AGENTS.md lacks the block or loses any of its text, CLAUDE.md is missing, or CLAUDE.md holds anything but the @AGENTS.md line; or in an empty repository CLAUDE.md lacks the block
- r2: A CLAUDE.md or AGENTS.md symlink that is dangling or points outside the repository is left alone with a warning naming the link and its target; a dangling CLAUDE.md counts as existing, so no new CLAUDE.md is written; a link inside the repository is written through once.
  Fails when: init creates or changes the target of a dangling link or of a link outside the repository, replaces such a link, writes a new CLAUDE.md beside a dangling one, gives no warning naming the link, or stops writing through CLAUDE.md -> AGENTS.md inside the repository
- r4: ADR 0011 has a dated Correction naming the @AGENTS.md case and the link rule, and init's help, the scaffold docstrings and docs/reference/commands.md say the same.
  Fails when: ADR 0011 has no Correction naming @AGENTS.md, or the help, docstrings or reference still say only that init writes CLAUDE.md when neither file exists
- r3: The other init tests still pass.
  Fails when: any test in tests/test_init.py fails
