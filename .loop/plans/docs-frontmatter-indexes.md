---
type: plan
title: 'Plan: docs-frontmatter-indexes'
description: Give docs/ per-folder indexes that kmctl check enforces and optional OKF staleness fields that review due reads, without making docs/ an OKF bundle.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T14:36:10+00:00'
slug: docs-frontmatter-indexes
epic: null
depends_on: []
priority: null
---

# docs-frontmatter-indexes

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none
<!-- When this ticket carries a finding raised while building another ticket,
replace "none" with that ticket's slug and the finding, in one line (ADR 0001). -->

## Intent

`docs/` gets two things from OKF without becoming a bundle (no
`okf_version`, no `log.md`, no `type`, Diataxis layout kept):

- Generated per-folder indexes. Each of `docs/tutorials/`, `docs/how-to/`,
  `docs/reference/` and `docs/explanation/` holds a `README.md` that kmctl
  generates from its pages: each page's H1 title as the link text, plus its
  `description` front matter when it has one. Nobody edits them by hand.
  `kmctl new doc` (`new_doc` in `src/kmctl/docs.py`) and `kmctl update`
  (`scaffold` in `src/kmctl/scaffold.py`) regenerate them, and
  `kmctl check --fix` regenerates them on demand, as `ruff --fix` does.
  `check_docs` in `src/kmctl/checks.py` fails (level `error`) when a
  folder index is missing or differs from what kmctl would generate, with
  "run `kmctl check --fix`" as the fix. `--fix` touches nothing else: not
  the root index, not a hand-written folder index, not `.okf/`.
  A generated index starts with a marker comment saying kmctl writes it.
  kmctl overwrites only a folder `README.md` that carries the marker or
  does not exist; a hand-written one is left alone and `check_docs` warns
  that kmctl does not manage it, so an upgrade never loses a user's text.
- A pre-commit hook. `new:.pre-commit-hooks.yaml` at the repo root offers
  hook `kmctl-check` (runs `kmctl check`, no file names passed) so another
  repo can list kmctl under `repos:` and add `args: [--fix]` to fix as it
  commits. This repo's `.pre-commit-config.yaml` runs it too.
- Agent instructions. The knowledge rule kmctl ships,
  `apm/claude/.apm/instructions/docs-layout.instructions.md` (and its
  generated Antigravity copy), the `CLAUDE.md`/`AGENTS.md` block in
  `src/kmctl/scaffold.py`, the auditor agent `apm/.apm/agents/kmctl-auditor.md`
  and the audit skill `apm/.apm/skills/audit/SKILL.md` say docs pages
  carry the optional front matter, that folder indexes are generated, and
  to run `kmctl check --fix` instead of editing one.
- Hand-written root index. `docs/README.md` stays free text and lists the
  folders. `kmctl update` keeps an existing one as is. When it has no link
  to a folder index, `check_docs` reports a new `warning` level next to
  `error` and `skipped` (`Finding.level` in `src/kmctl/checks.py`); a
  warning shows in the output and in the CI action's summary but does not
  fail `kmctl check`, so a downstream repo's CI stays green after an
  upgrade.
- Optional front matter on docs pages, using OKF v0.2 names: `description`,
  `stale_after`, `verified`, `sources`. A page may have none. `review_due`
  in `src/kmctl/review_due.py` lists docs pages that carry them, reading
  through `field` in `src/kmctl/okf.py`; `kmctl check` reports a field of the
  wrong shape. A docs page is due only when its `stale_after` has passed
  or a listed source changed; a missing `verified` does not make it due.
  `kmctl new doc` writes `description` (from `--description`),
  `stale_after` three months ahead and an empty `sources`, never
  `verified`. In `kmctl review due` a docs page's id starts with `docs/`
  (for example `docs/how-to/x`) so it cannot clash with an `.okf/`
  concept id; the `--json` shape does not change.

Invariant I4 changes, so the ticket adds an ADR with `kmctl new decision`
in `.okf/decisions/` and updates `.okf/manifesto.md`,
`.claude/rules/docs-layout.md`, `docs/reference/commands.md`, the docs page
schemas in `src/kmctl/kinds.py`, the briefing line in `src/kmctl/briefing.py`,
the write-docs skill `apm/.apm/skills/write-docs/SKILL.md`, and this repo's
`docs/`: today 6 pages in 4 folders, 0 folder indexes and 0 pages with
front matter. The migration gives every page a `description` taken from its
current `docs/README.md` entry. The migration writes `new:docs/tutorials/README.md`,
`new:docs/how-to/README.md`, `new:docs/reference/README.md` and
`new:docs/explanation/README.md`.

The outcome: on this repo after migration `kmctl check` passes with no
warnings, and in tests a folder index that differs from the generated one
gives exactly one error, a root index missing a folder link gives one
warning and exit 0, and a docs page past its `stale_after` appears in
`kmctl review due --json`.

## Could invalidate this plan

- none
