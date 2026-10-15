---
type: eval
title: 'Eval: schema-verbs'
description: 'Definition of done for schema-verbs: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T17:25:36+00:00'
slug: schema-verbs
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: db52083bea15ba18f7ac43120dbf53873b411e89b4b1f0bbb027ff2f31e2058d
  at: '2026-10-15T17:25:36+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl schema with no name lists every document kind with what it is for; an unknown kind is refused with that list.
  Fails when: the list lacks any of decision, practice, proposal, prototype, handoff, manifesto, index, section-index, log, architecture, tutorial, how-to, reference, explanation, docs-index; or an unknown kind exits 0 or does not list the kinds
- r2: kmctl schema KIND prints valid JSON Schema (draft 2020-12) whose properties are fields from ALLOWED_FIELDS only, each with a description; kinds with no front matter allow no properties (the root index only okf_version); the body is described in x-kmctl-sections as a section list, a heading pattern, or none.
  Fails when: for any kind the output is not valid draft 2020-12 JSON Schema, names a property not in ALLOWED_FIELDS or without a description, a no-front-matter kind allows a property, or x-kmctl-sections is missing
- r3: Everything kmctl init, kmctl new (each kind; with --stale-after for every kind and --source for every kind but handoff) and kmctl new doc (each type) writes matches its kind's schema, and this repository's own architecture page matches the architecture schema.
  Fails when: any file those verbs write, or .okf/architecture/overview.md, fails its kind's schema: front matter does not validate, or its ## sections differ from a fixed list, come in another order, or do not match a heading pattern
- r4: kmctl schema's help says the schema is built from kmctl's own table and is what kmctl writes, without claiming kmctl check or the validator enforce it; the briefing names kmctl schema within its word budget.
  Fails when: kmctl schema --help does not say the schema is built from kmctl's table and is what kmctl writes, or says kmctl check or the strict validator enforce it; the briefing does not name kmctl schema; or the briefing budget test fails
- r6: The per-kind table in src/kmctl/kinds.py is the one definition the writers and the schema read: skeletons, the manifesto's sections, status values and the architecture kind.
  Fails when: SKELETONS, the manifesto's section list, the status values or the architecture type and Depicts section are defined anywhere else in src/kmctl, or concepts.py, docs.py or scaffold.py does not import them from kinds.py
- r5: The other tests still pass.
  Fails when: any test fails
