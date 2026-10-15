---
type: eval
title: 'Eval: okf-fields-invariant'
description: 'Definition of done for okf-fields-invariant: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev77+gbd4712cf8.d20261015
  at: '2026-10-15T12:31:20+00:00'
slug: okf-fields-invariant
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 1dd6325468fd507a657cbcb73f90986dab0bd8b2f38f513b3580f6758474a190
  at: '2026-10-15T12:31:20+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Every front matter key kmctl's writing verbs write, nested keys as paths, is in okf.py's allowed list.
  Fails when: after init, new for each kind with and without --key, new doc and decision supersede in a scratch repository, any written key is not allowed; or the test still passes when an unknown key is added to a writer
- r2: Every front matter read in src/kmctl goes through okf.field with an allowed key, and a front_matter result is only ever passed as field's first argument.
  Fails when: the ast scan finds a field() key not in the allowed list, or a .get, subscript, in, or any use of a front_matter result other than as field's first argument
- r3: field() keeps today's forms: verified as one mapping or a list, sources entries as strings or mappings, and raises on a key that is not allowed.
  Fails when: field returns a different value for those forms than the code read before, or does not raise on an unknown key
- r4: kmctl check does not report [x](<a>b.md>) or [r]: <a>b.md> as broken links.
  Fails when: either form is reported
- r5: The manifesto marks I4 enforced by the two tests, with a log line, and the bundle passes the okf validator.
  Fails when: I4 still says planned, does not name the tests, has no log line, or the strict validator fails
