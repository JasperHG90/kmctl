---
type: eval
title: 'Eval: knowledge-check'
description: 'Definition of done for knowledge-check: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:41:22+00:00'
slug: knowledge-check
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: de2b17761814c08f96d83b4982691e2a856dc71c8a0be03270149d105e8779b0
  at: '2026-10-15T08:41:22+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl check passes on a repository whose docs/README.md and .okf/ indexes list every page, concept and section in the defined entry format.
  Fails when: kmctl check exits nonzero or reports a finding on the passing fixture
- r2: A page or concept with no entry in its index fails, naming the file.
  Fails when: kmctl check exits 0, or the finding does not name the unlisted file under check name index
- r3: An index entry whose file does not exist fails, naming the index and line.
  Fails when: kmctl check exits 0, or the finding lacks the index file and line
- r4: An .okf/ section not linked from the root index fails.
  Fails when: kmctl check exits 0 when a section folder has no root index link
- r5: A repository with no docs/ folder passes and reports docs as skipped.
  Fails when: kmctl check exits nonzero, or does not report docs as skipped
- r6: kmctl check --json prints a list of findings, each with check, file, line and message.
  Fails when: stdout is not a JSON list, or a finding lacks any of the four keys
