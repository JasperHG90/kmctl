---
type: eval
title: 'Eval: verify-verb'
description: 'Definition of done for verify-verb: 11 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T21:25:44+00:00'
slug: verify-verb
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: f8e51aae5029dcf209281ba911e0d371748fa9f50ec63065f29abbda486126c0
  at: '2026-10-17T21:25:44+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl verify ID --by human:ID appends a verified entry whose at is a full UTC timestamp to an unverified .okf/ concept, appends a line to .okf/log.md, and kmctl review due no longer lists that id, including when one of its sources was committed earlier the same day.
  Fails when: the concept still appears in kmctl review due after the verb exits 0 (with or without a same-day source commit), at is a bare date, the entry lacks by or at, or log.md gains no line naming the concept
- r2: kmctl verify takes a docs/ page id as kmctl review due prints it, writes the entry into that page's front matter, and a page listed for a source changed earlier the same day is no longer listed.
  Fails when: a docs page id is refused, the page has no verified entry afterwards, or kmctl review due still lists it
- r3: kmctl verify changes only the verified list: every other line of the file stays byte for byte, and an existing verified list keeps its entries with the new one appended.
  Fails when: any line outside the verified list differs, or an earlier verified entry is lost or reordered
- r4: kmctl verify refuses, with one line on stderr naming the fix and exit 1, when --by does not start with human:, the id matches no file, the id is a handoff, the front matter cannot be read, the file's stale_after has passed and no --stale-after is given, or --stale-after is not in the future; it writes nothing then.
  Fails when: any of those cases exits 0, prints the refusal on stdout, gives no fix, or changes a file
- r4b: kmctl verify ID --by human:ID --stale-after 6m on a concept listed as stale_after passed writes the new stale_after and the verified entry, and kmctl review due no longer lists it.
  Fails when: stale_after is unchanged or not the time --stale-after names, any other line changes, or kmctl review due still lists the id
- r5: kmctl verify --json prints one JSON object with id, path, by and at; the text output ends with a Next: kmctl review due line.
  Fails when: the JSON lacks a key or is not one object, or the text output has no Next: line naming kmctl review due
- r6: kmctl review due's text output ends with a Next: line naming kmctl verify (and --stale-after) when it lists anything due, prints no such line when nothing is due, and its --json output keeps its keys; the briefing tests still pass under TOKEN_BUDGET.
  Fails when: the due listing lacks a Next: line naming kmctl verify, the nothing-due output has one, the JSON gains or loses a key, or a briefing test fails
- r7: The audit skill and both okf-bundle rules (Claude and Antigravity) name kmctl verify and say an agent runs it only after the named person confirmed the concept.
  Fails when: any of the three files does not mention kmctl verify
- r8: kmctl verify --help passes the repository's help tests: one-line docstring, an example for every input, renders at 80 columns.
  Fails when: any help test fails
- r9 (judgment): A new ADR records that kmctl verify writes a person's check and an agent may run it only on that person's confirmation, without changing ADR 0005 or I2; docs/reference/commands.md and the architecture overview's Depicts list name the verb.
  Fails when: no ADR covers the verb, the wording lets an audit verdict alone trigger it, or the reference or Depicts list omits it
- r10: The full lint and test gates pass, including the APM package body-hash test the rule edit changes.
  Fails when: just lint or just test exits nonzero
