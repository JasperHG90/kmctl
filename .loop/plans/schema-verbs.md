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

- `kmctl schema` with no name lists the document kinds, one line each with what it is for. `kmctl schema KIND` prints one JSON Schema (draft 2020-12) object for that kind, covering:
  - concepts `kmctl new` writes: decision, practice, proposal, prototype, handoff;
  - bundle files `kmctl init` writes: manifesto, the root index, section indexes, the log;
  - architecture pages, which no verb writes, with their `## Depicts` section;
  - docs pages by type: tutorial, how-to, reference, explanation, and the docs index.
- Each schema's `properties` are the front matter fields that kind uses, taken from `ALLOWED_FIELDS` (I4), with `required` and the values a field may take (such as `type`'s value, `status` values, the `stale_after` timestamp format, `sources` as `resource` mappings, `handoff_key` for handoffs only), and each field's `description` from where it comes from (the OKF section or the ADR). The body's expected `##` sections, in order, go in an `x-kmctl-sections` keyword, taken from the same skeleton lists `kmctl new` and `kmctl new doc` write (`SKELETONS` in `concepts.py` and `docs.py`), with notes where the rules say more (a decision names its rejected alternative inside Decision; a correction is an appended dated section).
- Built from the code when it runs, so the schema and what kmctl writes cannot drift. `--help` says what the schema is and that it is what `kmctl check` and the strict validator expect. The briefing's verb line names `kmctl schema`, within its word budget.

Measured: kmctl has 0 commands that state a document's shape; an agent learns it from 9 one-line rules and the skeletons, and the architecture page kind has no skeleton or verb at all.

Done when tests show `kmctl schema` lists every kind; `kmctl schema KIND` prints valid draft 2020-12 JSON Schema for each; every file `kmctl init`, `kmctl new` (each kind, with and without `--stale-after` and `--source`) and `kmctl new doc` (each type) writes has front matter that validates against its kind's schema and the `##` sections its `x-kmctl-sections` lists in that order; a field not in `ALLOWED_FIELDS` appears in no schema; an unknown kind is refused with the list; and the briefing stays within its budget.

## Could invalidate this plan

- none
