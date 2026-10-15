---
type: eval
title: 'Eval: schema-verbs'
description: 'Definition of done for schema-verbs: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T17:22:43+00:00'
slug: schema-verbs
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 1451b5bfcb0ea1722634979ee83616ee8145901d725fdbe62ff7af81c2c200b8
  at: '2026-10-15T17:22:43+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl schema with no name lists every document kind with what it is for; an unknown kind is refused with that list.
  Fails when: the list lacks any of decision, practice, proposal, prototype, handoff, manifesto, index, section-index, log, architecture, tutorial, how-to, reference, explanation, docs-index; or an unknown kind exits 0 or does not list the kinds
- r2: kmctl schema KIND prints valid JSON Schema (draft 2020-12) whose properties are fields from ALLOWED_FIELDS only, with required, allowed values and descriptions, and the body's expected sections in x-kmctl-sections.
  Fails when: for any kind the output is not valid draft 2020-12 JSON Schema, names a property not in ALLOWED_FIELDS, has a property without a description, or lacks x-kmctl-sections
- r3: Everything kmctl init, kmctl new (each kind, with and without --stale-after and --source) and kmctl new doc (each type) writes matches its kind's schema: front matter validates and the ## sections appear in the listed order.
  Fails when: any file those verbs write fails its kind's schema, or its ## sections differ from x-kmctl-sections or come in another order
- r4: kmctl schema's help says what the schema is and where it comes from, and the briefing names kmctl schema within its word budget.
  Fails when: kmctl schema --help does not say the schema is built from kmctl's code and is what kmctl check and the strict validator expect, the briefing does not name kmctl schema, or the briefing budget test fails
- r5: The other tests still pass.
  Fails when: any test fails
