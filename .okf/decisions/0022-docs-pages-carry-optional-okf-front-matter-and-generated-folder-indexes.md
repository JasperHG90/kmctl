---
type: decision
title: "ADR 0022: Docs pages carry optional OKF front matter and generated folder indexes"
description: "docs/ pages may carry the OKF fields description, stale_after, verified and sources, and each Diataxis folder gets a README.md index that kmctl check --fix generates, without docs/ becoming an OKF bundle."
tags: [decision]
generated:
  by: process:kmctl/0.3.0
  at: 2026-10-17T16:57:28Z
status: stable
sources:
  - resource: "src/kmctl/docs_index.py"
  - resource: "src/kmctl/checks.py"
  - resource: "src/kmctl/review_due.py"
---

# ADR 0022: Docs pages carry optional OKF front matter and generated folder indexes

## Context

`docs/` is for people who use a project, and `.okf/` for people and agents
working on it ([ADR 0006](0006-staleness-from-okf-fields.md) and the
manifesto's table). Only `.okf/` concepts carried the fields that say when a
page goes stale, so `kmctl review due` could never point at a user page that
had drifted from the code. And `docs/README.md` had to list every page by
hand, which grows into one long list and has to be kept in step on every new
page.

The operator asked (2026-10-17) for docs pages to carry that front matter
and for indexes that help people find their way, without making `docs/` a
full OKF bundle. They then asked for `kmctl check` to fail on a docs folder
with no `README.md`, for a `--fix` flag like ruff's that writes them, and for
a pre-commit hook that runs it.

## Decision

`docs/` borrows OKF's fields and its per-section indexes, and nothing else.

- **Front matter.** A docs page may carry `description`, `stale_after`,
  `verified` and `sources`, with their OKF v0.2 meanings and shapes. All four
  are optional; a page with none is fine. `kmctl check` fails on a field of
  the wrong shape. `kmctl new doc` writes `description`, a `stale_after`
  three months ahead and an empty `sources`, and never `verified`.
- **Due for review.** `kmctl review due` lists a docs page once its
  `stale_after` passes, or once a source is committed after the page's last
  `verified` date or, with none, after the page's own last commit. This
  amends ADR 0006 for docs pages only: a missing `verified` does not make a
  docs page due, because a user page is checked by being edited, and every
  new page would otherwise sit in the briefing's due list. A docs page's id
  starts with `docs/` so it cannot clash with a concept id.
- **Generated folder indexes.** Each Diataxis folder's `README.md` is
  generated from its pages: each page's `#` title and its `description`,
  under a marker line. A script can write it, so a script does (prompts may,
  code must). `kmctl check` fails when one is missing or out of date, and
  `kmctl check --fix`, `kmctl new doc` and `kmctl update` write it. kmctl
  rewrites only a file with its marker: a folder `README.md` someone wrote by
  hand is kept, with a warning, and checked like any index.
- **Hand-written root index.** `docs/README.md` is where a person explains
  the docs, so it stays free text. It must list any page outside the four
  folders, and `kmctl check` warns, through a new `warning` level that does
  not fail the check, when it does not link a folder's index.
- **Pre-commit hook.** The repository's `.pre-commit-hooks.yaml` offers
  `kmctl-check`, which runs `kmctl check` once per commit;
  `args: [--fix]` rewrites the indexes as you commit.

Rejected:

- Making `docs/` an OKF bundle (an `okf_version` index, a `log.md`, a `type`
  on every page). Diataxis sorts by what the reader wants to do, OKF types by
  kind of knowledge, and user pages would show YAML they never asked for.
  The split between `docs/` and `.okf/` is by reader, and a bundle would blur
  it.
- One flat `docs/README.md` listing every page, as before. It works for six
  pages, not sixty, and it is a list a person must keep in step by hand.
- A separate `kmctl docs index` command. `kmctl check --fix` is the one way
  in, the way `ruff check --fix` is.
- A warning, not an error, for a missing folder index. The operator wants the
  check to fail on it. A repository that bumps kmctl without running
  `kmctl update` or `kmctl check --fix` fails once, with that fix in the
  message.
- Rewriting the root index on upgrade. It is the user's text; kmctl only
  warns about the folder links it lacks.

## Consequences

- Invariant I4 now covers docs pages: kmctl reads the same four OKF fields
  there, through `okf.field`, and no new field.
- `kmctl review due` reads `docs/` even in a repository with no `.okf/`.
- Downstream CI goes red once after an upgrade until someone runs
  `kmctl update` or `kmctl check --fix`; the error says so.
- A hand-written folder index is never overwritten, but nothing checks that
  its descriptions match the pages.
- Agents and people never edit a folder index; the knowledge rules, the
  `CLAUDE.md` block and the `write-docs` skill say to run `kmctl check --fix`.
