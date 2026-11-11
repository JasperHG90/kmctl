---
type: plan
title: 'Plan: agent-audit-claims'
description: A claims store in SQLite inside the repository (git-ignored) with the Pydantic claim schema, kmctl claims todo/submit/list for agents, and change detection by section.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-11T07:24:30+00:00'
slug: agent-audit-claims
epic: agent-audit
depends_on: []
priority: 2
schema_version: '2.0'
---


# agent-audit-claims

Relayed from: none

## Intent

Ticket 1 of the agent-audit epic. Claim extraction moves out of the
prototype (`.okf/prototypes/audit-cli/`, a standalone Typer CLI on langchain,
langgraph and alembic that needs a model key) into kmctl proper, as CLI verbs
a coding agent can drive. The skill and the Haiku subagent that drive them
are the next ticket, agent-audit-claims-skill. Later tickets build on both:
agent-audit-checks (check DSL, `kmctl checks ...`), agent-audit-extract
(automatic `kmctl claims extract` behind a `kmctl[audit]` extra) and
agent-audit-decide (optional `kmctl decide`). None of their verbs land here.

What lands:

- **The schema.** The prototype's claim models (claims/models.py there:
  `SentenceVerdict`, `ClaimText`, `Verdicts`, the stored `Claim`, `claim_id`)
  become `new:src/kmctl/claims/models.py`. `kmctl claims submit` validates an
  agent's answer against these models, and agent-audit-extract will validate
  model output against the same ones, so the two paths cannot drift.
- **Sections and change keys.** The prototype's chunker (processing/chunker.py)
  becomes `new:src/kmctl/claims/sections.py`, rewritten on the standard
  library and kmctl's own front matter reader (`src/kmctl/okf.py`): header
  split with `re` that ignores `#` inside code fences, the same sentence
  splitter, the same section ids (`concept#slug`), the same section key
  (header path, sentences, corrections, type) and extraction key (plus id,
  title, status, earlier sections). The key also covers a hash of the
  extraction instructions, so changing them hands every section out again.
  Front matter reads go through `okf.field`, as I4 and
  `tests/test_okf_fields.py` require; `type`, `title` and `status` are OKF
  spec fields, so I4 needs no new extension field. Bundle discovery follows
  the prototype's target.py (a repository with `.okf/`, a bundle folder, or
  one concept file).
- **The instructions.** The prototype extractor's SYSTEM_PROMPT, reworded only
  where it addresses a model call instead of an agent, becomes
  `new:src/kmctl/claims/instructions.py`. `kmctl claims todo --json` hands it
  out with the sections, so the instructions live once, in the CLI, and the
  next ticket's skill and agent stay thin (`.claude/rules/skills-are-thin.md`).
- **The store.** `new:src/kmctl/claims/store.py` on stdlib `sqlite3`: tables
  for sections, extractions (one per section extraction key and instructions
  hash, recording who submitted it), sentence verdicts and claims. Schema
  versions move by ordered SQL steps tracked in `PRAGMA user_version`, in
  place of the prototype's Alembic revisions, so later tickets add tables
  the same way. WAL mode and a busy timeout let parallel subagents submit at
  once.
- **Where the store lives (the operator's decision).** In the repository,
  git-ignored: .kmctl/audit.sqlite at the repository root (git's top level,
  else the bundle's parent), named for the whole audit because later tickets
  add their tables to it. When kmctl creates .kmctl/ it also writes
  .kmctl/.gitignore holding `*`, so the folder ignores itself, `.gitignore`
  included, and kmctl never edits the user's own `.gitignore`. Each checkout
  and each loop worktree has its own store. Rejected: a per-user data folder
  (the prototype's choice; invisible from the repository and out of reach of
  CI and later tickets) and a committed database file (binary churn in every
  diff and merge conflicts on every pass).
- **I2 for the claims verbs.** They write only under .kmctl/, which git
  ignores; never `.okf/` or `docs/`, and never a `verified` stamp. The claims
  store is audit state, not knowledge.
- **The verbs**, a new `kmctl claims` group in `src/kmctl/__init__.py`
  following `.claude/rules/cli-interface.md` and
  `.claude/rules/interface-audience.md` (audiences: an extraction subagent
  first, a person checking progress second, scripts through `--json`):
  - `kmctl claims todo [PATH] [--limit N] --json` cuts the bundle, refreshes
    the store's sections, drops the claims of sections whose text changed or
    that are gone, and lists the sections with no extraction for their
    current key: id, key, concept, title, section, numbered sentences,
    earlier sections and corrections, with the instructions once at the top.
    Without `--json` it prints counts (up to date, new, changed, removed) for
    a person. It ends with `Next: kmctl claims submit`.
  - `kmctl claims submit [FILE|-] --json` reads an answer (section id, the key
    `todo` gave, verdicts), validates it against the models, refuses a stale
    key (naming `kmctl claims todo`) and an answer that leaves a sentence
    without a verdict (naming the missing numbers), and otherwise stores the
    verdicts and claims. A refusal is one stderr line with the fix and a
    nonzero exit; one bad section does not undo the good ones in the same
    file.
  - `kmctl claims list [PATH] [--kind KIND] [--claims] --json` reads the
    store: documents with sections and claims per kind, or each claim with
    its sentence, kind, quantifier, how to check and reason.
- **The record.** A decision record in this change, written with `kmctl new
  decision`: claims are extracted through `kmctl claims` verbs, validated by
  one Pydantic schema, into a git-ignored SQLite store in the repository.
  Rejected: keeping the prototype standalone, its dependencies in base
  kmctl, a per-user data folder, and a committed database file. It relates
  to ADR 0005 (audits report only) and ADR 0017 (the CI audit script, which
  this does not change: `action/agent.py` and the `audit` skill stay as they
  are). `.okf/manifesto.md` Parts names the new verbs;
  `.okf/architecture/overview.md` gains the claims flow;
  `docs/reference/commands.md` documents the three verbs and the store,
  landing with the behaviour (`.claude/rules/docs-layout.md`).

Base kmctl stays at its four dependencies: nothing here needs more than the
standard library, pydantic and pyyaml.

**Measured effect of change detection.** Over the 66 commits since
2026-10-15 that changed a concept in this repository's `.okf/` (git log,
index, log and prototype files left out), the median commit changed 2 of
the bundle's 38 concepts (mean 2.9, max 9). So on a typical pass `todo`
hands out about 5% of concepts instead of all of them; at section level,
finer still. The prototype counted 156 sections from 31 concepts and about
three model calls a section on this bundle (its README, 2026-11-08), so
skipping unchanged sections is the difference between a pass that reads a
few sections and one that reads them all.

**The outcome that shows it worked:** in a fixture repository, a scripted
agent calls `kmctl claims todo --json`, then `kmctl claims submit -`, and
`kmctl claims list --json` returns the claims; a second `todo` lists nothing;
editing one section lists only that section; and no tracked or unignored
file changed.

The operator commits the prototype folder to main before building; until
then it is untracked, so its files are named here in prose, not as paths.

## Problems

- P1: Claim extraction lives only in an untracked prototype that needs langchain and a model key, so no coding agent can drive it through kmctl
- P2: Nothing stores claims per project or knows which sections changed, so every pass would read the whole bundle while the median bundle commit changes 2 of 38 concepts
- P3: No claim schema is enforced on what an agent writes, so agent claims and the later automatic extractor's claims could take different shapes

## Goals

- G1: A coding agent extracts a bundle's claims through kmctl verbs, with base kmctl's dependencies unchanged
- G2: Claims live in one per-project store, in one validated shape that later tickets reuse
- G3: A second pass hands out only the sections whose text changed

## Outcomes

### O1: Base kmctl holds the claim models, the extraction instructions and a stdlib section cutter with change keys
- kind: support
- goal: G3
- fixes: P3
- needs: none
- touches: `new:src/kmctl/claims/__init__.py`, `new:src/kmctl/claims/models.py`, `new:src/kmctl/claims/sections.py`, `new:src/kmctl/claims/instructions.py`
- checked by: `new:tests/test_claims_sections.py` (fixture bundle: section ids, sentence splits, code fences kept whole, correction context, deprecated concepts skipped, keys change with text, title and instructions) and `tests/test_okf_fields.py` still green
- seen by: calling code

### O2: A git-ignored SQLite store at .kmctl/audit.sqlite, with versioned schema steps
- kind: support
- goal: G2
- fixes: P2
- needs: O1
- touches: `new:src/kmctl/claims/store.py`
- checked by: `new:tests/test_claims_store.py` (store at the repository root, .kmctl/.gitignore holds `*` and `git status --porcelain` stays empty after a write, a fresh and an older-version database both open at the newest version, two writers at once)
- seen by: calling code

### O3: The `kmctl claims` group lets an agent take sections with `todo`, store its answer with `submit` and read claims back with `list`
- kind: behaviour
- goal: G1
- fixes: P1
- needs: O1, O2
- touches: `kmctl claims todo`, `kmctl claims submit`, `kmctl claims list`, `src/kmctl/__init__.py`
- checked by: `new:tests/test_claims_cli.py` (todo: first run lists every section, after submits none, an edited section is the only one listed and its old claims are gone, a removed concept's claims are gone; submit: a valid answer is stored, a stale key, a missing sentence verdict and a malformed answer each refuse with one stderr line naming the fix, good sections in a mixed file are kept; list: counts per kind, one concept's claims, `--kind`, `--json` shape; no tracked or unignored file changes after any verb) and `tests/test_help.py`
- seen by: operator

### O4: A decision record, the manifesto, the architecture overview and the command reference describe the claims verbs and store
- kind: support
- goal: G1
- fixes: P1
- needs: O3
- touches: `.okf/manifesto.md`, `.okf/architecture/overview.md`, `.okf/decisions/index.md`, `.okf/summary.md`, `.okf/log.md`, `docs/reference/commands.md`
- checked by: `kmctl check`, strict OKF validation in the pre-commit hooks, and the docs tests
- seen by: operator

## Could invalidate this plan

- none
