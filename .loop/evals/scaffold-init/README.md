---
type: eval
title: 'Eval: scaffold-init'
description: 'Definition of done for scaffold-init: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:32:33+00:00'
slug: scaffold-init
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: fe60ca38721afe1815e66302de6480d474ec12001bc576942189a510bf041c72
  at: '2026-10-15T08:32:33+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In an empty repository, kmctl init creates docs/README.md, .okf/index.md, .okf/log.md and .okf/manifesto.md, and prints each path it created.
  Fails when: any of the four files is missing after the run, or a created path is not printed
- r2: A second kmctl init changes nothing and reports nothing created.
  Fails when: any file's content or mtime differs after the second run, or the second run reports a created path
- r3: kmctl init never overwrites a file that already exists.
  Fails when: a pre-existing docs/README.md or .okf/manifesto.md has different content after the run
- r4: The bundle kmctl init creates passes the pinned okf validator in strict mode.
  Fails when: tests/vendor/okf_validate.py --strict exits nonzero on the created .okf/
- r5: kmctl init creates no Diataxis folders and no .okf/ section folders.
  Fails when: any directory exists under docs/ or .okf/ after the run
- r6: kmctl init --json prints one JSON object listing created and skipped paths.
  Fails when: stdout is not one JSON object with created and skipped lists
