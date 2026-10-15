---
name: schema-versioning
description: How a change to a data model in stores/models.py is versioned, and which reads may drop unknown keys. Read before changing a model's fields or adding a reader of one.
paths: ["src/kmctl/stores/**", "src/kmctl/evidence/**", "src/kmctl/verdicts/**", "src/kmctl/gates/**", "src/kmctl/commands/**", "src/kmctl/hooks/**"]
---

# Schema versions

Each of the 10 data models extends `Versioned` and carries a MAJOR.MINOR
`schema_version`; a file without it reads as 1.0, and loopctl writes its own
version (ADR 0039).

WHY: four migrations shipped with no version to mark them (`state
migrate-config`, `migrate-evals`, `migrate-tickets`, `migrate-verdicts`,
ADRs 0024, 0027, 0034, 0036). Each sniffs the file's shape, and the move
to JSON tickets could not go through `ticket land`: its stamp met the old
ledger and failed on a shape error instead of naming the migration.

<constraint name="bump-with-the-change">
Keep a model change backward compatible where you can. An added optional
field or a widened value bumps the minor in `SCHEMA_VERSION`. A removed or
renamed field, a narrowed type or a new required field bumps the major and
ships its `loopctl state migrate-*` verb in the same change, named in
`MIGRATE_VERB`.
</constraint>

<constraint name="strict-unless-read-only">
Reads are strict by default. A lenient read, which drops a newer minor's
unknown keys, is only for a caller that never writes the object and never
decides a gate with it (the reports: `status`, `ticket list`, `graph` and
the like), and it asks for one through the store's explicit option, for
example `tickets.load(paths, slug, read_only=True)`. Every verb that writes
the object, every input a record is built from (fix summary, verdict front
matter, eval rows on sign) and every gate or hook stays strict, because a
dropped field there could run a laxer gate or vanish on the next save.
`Config` is strict at every version and has no lenient read.
</constraint>

The `.loop/events/` streams are the one exception: they are append-only, so
event readers accept every version and no event kind has a migrate verb
(ADR 0039's correction).

Who owns each store is `.claude/rules/data-management.md`.
