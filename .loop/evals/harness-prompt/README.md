---
type: eval
title: 'Eval: harness-prompt'
description: 'Definition of done for harness-prompt: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T05:57:02+00:00'
slug: harness-prompt
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 7434b0d056304315bf08f07fa72584631849f5c9b96620d80f4c37c6add2a1a0
  at: '2026-10-17T05:57:02+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: With stdin a terminal and no --harness, kmctl plugin install writes to stderr a question listing each harness in HARNESSES with a number, reads a comma list of numbers or names, and installs exactly the harnesses the answer names; an empty answer installs claude; an answer naming no known harness is asked again, naming the accepted values; stdout holds no part of the question.
  Fails when: no question is asked, the question goes to stdout, the APM --target differs from the answer, an empty answer installs anything but claude, or a bad answer is accepted or ends the command
- r2: kmctl plugin update with stdin a terminal and no --harness asks the same question, with the harnesses doctor's harnesses_found finds installed at that scope as its default (claude when none is found), and an empty answer updates those.
  Fails when: update asks no question, or an empty answer in a repository with antigravity installed (or claude and antigravity) updates a different set
- r3: Without --harness, when stdin is not a terminal or --json is given, install and update refuse with exit 1 and a message naming --harness and the accepted values, without prompting and without running APM; with --harness they never prompt.
  Fails when: the command prompts, exits 0, runs APM, or its message does not name --harness and every harness; or a run with --harness prompts
- r4: kmctl plugin install --help and update --help, docs/reference/commands.md and both install how-tos say that without --harness the command asks at a terminal and refuses otherwise, and what update's default is.
  Fails when: the help or any of those pages still says the default is claude or does not mention the question
- r5: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
