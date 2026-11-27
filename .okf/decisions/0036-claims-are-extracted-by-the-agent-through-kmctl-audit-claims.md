---
type: decision
title: "ADR 0036: Claims are extracted by the agent through kmctl audit claims"
description: "A coding agent's own model extracts a bundle's claims through kmctl audit claims todo, submit and list, validated by one Pydantic schema into a git-ignored SQLite store at .kmctl/audit.sqlite; the CLI makes no model call."
tags: [decision]
generated:
  by: process:kmctl/0.12.1
  at: 2026-11-11T09:05:54Z
status: stable
sources:
  - resource: "packages/kmaudit/src/kmaudit/"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
---

# ADR 0036: Claims are extracted by the agent through kmctl audit claims

## Context

Claim extraction lived in a prototype, `.okf/prototypes/audit-cli/`: a
standalone Typer CLI on langchain, langgraph and alembic that needs a model
key. No coding agent could drive it through kmctl, nothing kept claims per
repository, and every pass would read the whole bundle. Over the 66 commits
since 2026-10-15 that changed a concept in this repository's `.okf/`, the
median commit changed 2 of 38 concepts, so a pass that skips unchanged
sections reads about 5% of the bundle.

## Decision

- A coding agent extracts claims with its harness's own model, through a
  new `kmctl audit` group: `kmctl audit claims todo` hands out the sections
  with no extraction for their current key, with the instructions once;
  `kmctl audit claims submit` validates an answer against one Pydantic
  schema (`src/kmctl/claims/models.py`) and stores it; `kmctl audit claims
  list` reads claims back. The CLI makes no model call.
- A section's key covers its text, its concept's id, title, status and
  type, the earlier sections and a hash of the instructions
  (`src/kmctl/claims/instructions.py`), so changing any of them hands it
  out again and drops its old claims.
- The store is SQLite on the standard library, at `.kmctl/audit.sqlite` in
  the repository root (git's top level, else the bundle's parent). kmctl
  writes `.kmctl/.gitignore` holding `*`, so the folder ignores itself and
  the user's own `.gitignore` is never edited. Schema steps are ordered SQL
  tracked in `PRAGMA user_version`; WAL mode and a busy timeout let parallel
  agents submit at once. Each checkout and worktree has its own store.
- The claims verbs write only under `.kmctl/`: never `.okf/` or `docs/`,
  and never a `verified` stamp (I2).

Rejected:

- Keep the prototype standalone: no agent could reach it through kmctl.
- Its dependencies in base kmctl: langchain and langgraph for two fixed
  steps; base kmctl keeps httpx, pydantic, pyyaml and typer.
- A model call inside the CLI: the agent already has a model, and a key in
  kmctl is one more secret to hold.
- A per-user data folder (the prototype's choice): invisible from the
  repository and out of reach of CI and later tickets.
- A committed database file: binary churn in every diff and a merge
  conflict on every pass.

## Consequences

The CI audit ([ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md))
does not change: `action/agent.py` and the `audit` skill stay as they are,
and audits still report only ([ADR 0005](0005-audits-report-only.md)).
A claim may cite earlier sentences of its concept, so the earlier sections
are in a section's key: editing one section also hands out the sections
after it in the same concept. A fresh checkout has no claims until an agent extracts them. Later tickets
add their tables to the same store as further schema steps.

## Correction, 2026-11-11

[ADR 0040](0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording.md):
a claim's id still follows its text, but a stored check or reason now
follows a reworded claim of the same sentence, so re-extracting an edited
section keeps its answers.

## Correction, 2026-11-14

The verbs this record names as `kmctl audit claims` are `kmaudit claims`
now: the audit left kmctl for its own package, kmaudit, in
`packages/kmaudit/` (ADR 0043). The rest of this record stands.
