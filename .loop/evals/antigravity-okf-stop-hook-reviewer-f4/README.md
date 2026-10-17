---
type: eval
title: 'Eval: antigravity-okf-stop-hook-reviewer-f4'
description: 'Definition of done for antigravity-okf-stop-hook-reviewer-f4: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T08:09:26+00:00'
slug: antigravity-okf-stop-hook-reviewer-f4
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 596b0080f188ea6ee7e5f5c8bd517ceaab91363821a60e4617c7b54123dd7dbe
  at: '2026-10-17T08:09:26+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl doctor's antigravity.apm-hooks fails, naming .agents/hooks.json, that it is not a JSON object, and a fix to repair the file by hand and run kmctl plugin install --harness antigravity, when that file does not parse; it passes for a parsed file whose handlers do not run okf-stop-check.sh, even when the text mentions it elsewhere; and it still fails, naming kmctl plugin install --harness antigravity, for a handler that runs it.
  Fails when: an unparsable file passes or gets only the install fix, a mention outside a handler command fails the check, or an okf handler passes
- r2: docs/reference/commands.md describes the unparsable-file case of antigravity.apm-hooks; the install how-to's sample doctor output includes an antigravity.apm-hooks line, and its copy of the install note names okf's Stop check as the CLI prints it.
  Fails when: the reference lacks the case, the sample output lacks the line, or the note differs from the CLI's
- r3: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
