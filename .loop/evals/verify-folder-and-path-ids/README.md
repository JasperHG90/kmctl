---
type: eval
title: 'Eval: verify-folder-and-path-ids'
description: 'Definition of done for verify-folder-and-path-ids: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-27T09:51:11+00:00'
slug: verify-folder-and-path-ids
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: a7204dfe5aa90e6ea676000b812b74ca919d2914b0735bb1418f4499e87416c6
  at: '2026-11-27T09:51:11+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl verify decisions, in a repository with three decision records, a decisions index and a log, writes one verified entry and one log line per record and exits 0
  Fails when: the exit code is nonzero, a record lacks the entry, a log line is missing, or the decisions index changes by one byte
- r2: a docs folder id (docs/how-to) verifies every docs page under it and leaves its README.md index alone
  Fails when: a page under the folder lacks the entry, a page outside it gains one, or the README.md changes
- r3: a repository-root path with .md (.okf/decisions/0001-x.md, docs/how-to/x.md) verifies the same file its id would, and prints the id as kmctl review due does
  Fails when: either path is refused, or the printed id differs from the one review due lists
- r4: an id for a file kmctl review due never lists (decisions/index, .okf/decisions/index.md, log) or the handoffs folder is refused, exits 1 and writes nothing
  Fails when: any of them exits 0, or any file in the repository changes
- r5: a refusal for decisions/* and for decisions/index names the command kmctl verify decisions
  Fails when: the refusal on stderr does not contain 'kmctl verify decisions'
- r6: kmctl verify --help names the folder form and the path form in its argument help and gives a folder example in its epilog, and the help tests stay green
  Fails when: the help lacks a folder id or a path with .md, or a test in test_help.py fails
- r7 (judgment): a draft decision record states the folder form and why it does not undo ADR 0055's rejection, and ADR 0055 has a correction pointing at it
  Fails when: the record is missing, is not linked from the decisions index, or ADR 0055 has no correction naming it
