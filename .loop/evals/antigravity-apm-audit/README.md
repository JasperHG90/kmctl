---
type: eval
title: 'Eval: antigravity-apm-audit'
description: 'Definition of done for antigravity-apm-audit: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T16:27:57+00:00'
slug: antigravity-apm-audit
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: abae0efae4c524d9fd78dccc88c3f4ff1d53326fb0ebd2c098070d89ecf20938
  at: '2026-10-19T16:27:57+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: A starter project bootstrapped for claude and antigravity passes apm audit --ci --no-drift --no-policy (exit 0) after install and kmctl plugin patch. OpenCode is out: APM's content-integrity check flags the agents kmctl plugin patch rewrites, and no audit flag skips it; the install how-to says so and the drift gate covers OpenCode.
  Fails when: the audit exits nonzero for the claude and antigravity project
- r2: The starter justfile has a recipe that runs a frozen install, kmctl plugin patch, and fails when git status --porcelain prints anything; on a fresh clone of the committed project it exits 0, and after a committed one-line edit to an installed skill it exits nonzero.
  Fails when: the recipe is missing from the rendered justfile, exits nonzero on the clean clone, or exits 0 after the committed edit
- r3: kmctl's MCP server is named bundle everywhere it is declared or checked, and no source, doc or test outside .loop/ and the okf-bundle rule names still uses okf-bundle for the server.
  Fails when: apm/apm.yml or MCP_NAME is not bundle, or the package tests fail
- r4: Doctor passes a bundle server that runs okf's script but not kmctl's launcher, and fails a bundle server that runs no okf script.
  Fails when: either case gets the other outcome
- r5 (judgment): The install how-to says CI runs apm audit --ci for a Claude Code-only install and apm audit --ci --no-drift plus the gate for Antigravity (and OpenCode if drift fires there), and ADRs 0014, 0018, 0019 and 0020 carry dated corrections or consequences for the rename and the drift; drop_old_mcp is gone.
  Fails when: the docs give no working CI gate per harness, a correction is missing, or drop_old_mcp still exists
