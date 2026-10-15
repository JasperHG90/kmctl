---
type: plan
title: 'Plan: schema-verbs'
description: "A kmctl schema command group prints the expected shape of each kind of document kmctl knows (concepts, bundle files, architecture pages, docs pages): its front matter as JSON Schema and its body sections, built from kmctl's own code so it cannot drift."
slug: schema-verbs
epic: knowledge
depends_on: [new-concept-freshness]
priority: 4
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T17:22:30+00:00'
---

# schema-verbs

Relayed from: operator, 2026-10-15: "add a 'schemas' sub command group (like loopctl has) that contains expected schema for each doc".

## Intent

An agent writing an `.okf/` concept or a `docs/` page today learns its shape from the rules, the skeleton `kmctl new` writes, or by copying a neighbour. Nothing states it. loopctl answers the same need with `loopctl schema NAME`, which prints JSON Schema built from its own models; kmctl gets the same, named `kmctl schema` to match.

- `kmctl schema` with no name lists the document kinds, one line each with what it is for. `kmctl schema KIND` prints one JSON Schema (draft 2020-12) object for that kind: concepts `kmctl new` writes (decision, practice, proposal, prototype, handoff); bundle files `kmctl init` writes (manifesto, root index, section index, log); architecture pages, which no verb writes; and docs pages by type (tutorial, how-to, reference, explanation) and the docs index.
- One table in `new:src/kmctl/kinds.py` holds, per kind: the front matter fields it uses and which are required (field names only from `ALLOWED_FIELDS`, I4), the allowed values (each kind's `type`, the `status` values draft, stable and deprecated from OKF v0.2), and its body: a fixed list of `##` sections, a heading pattern, or none. The writers read the same table: `kmctl new` and `kmctl new doc` take their skeletons from it (the `SKELETONS` lists move there), `kmctl init` takes the manifesto's sections from it, and the architecture kind's `type` and closing `## Depicts` section live there too, so the rule file and the schema name the same thing (round 1 plan review). What only a rule says, such as a decision naming its rejected alternative inside Decision, goes in the schema's description, not as a check.
- Kinds with no front matter say so: the docs pages, the docs index, section indexes and the log have a schema that allows no properties (the root index allows only `okf_version`), so a reader is told plainly rather than handed an empty schema. The log's body is described by its heading pattern (dated `## YYYY-MM-DD` sections of lines), not a fixed list, in `x-kmctl-sections` as `{"pattern": ...}`.
- `kmctl schema --help` says the schema is built from kmctl's own table when it runs, so it is what kmctl writes; it does not claim `kmctl check` or the validator enforce it, since neither checks per-kind fields or sections. The briefing's verb line names `kmctl schema`, within its word budget.

Measured: kmctl has 0 commands that state a document's shape; an agent learns it from 9 one-line rules and the skeletons, and the architecture kind has no skeleton or verb at all. The status values exist only in the vendored validator, and the manifesto's sections only inside a string in `scaffold.py`.

Done when tests show `kmctl schema` lists every kind; `kmctl schema KIND` prints valid draft 2020-12 JSON Schema for each, every property a field from `ALLOWED_FIELDS` with a description, and no-front-matter kinds allowing no properties; everything `kmctl init`, `kmctl new` (each kind; with `--stale-after` for every kind and `--source` for every kind but handoff) and `kmctl new doc` (each type) writes matches its kind's schema, front matter and sections; this repository's own architecture page matches the architecture schema; the skeleton, manifesto-section and architecture constants each have one definition in `src/kmctl/kinds.py` that the writers import; an unknown kind is refused with the list; and the briefing stays within its budget.

## Could invalidate this plan

- none
