---
type: plan
title: 'Plan: readmes-per-package'
description: The root README becomes a short map to the two package READMEs and docs/, kmctl's README carries its install and use, and kmaudit's command reference moves into the root docs/.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T18:42:41+00:00'
slug: readmes-per-package
epic: monorepo-release
depends_on: []
priority: 1
schema_version: '2.0'
---

# readmes-per-package

Relayed from: none

## Intent

The operator, in order: "kmaudit docs still in packages/kmaudit. We said
that all docs go to root" (earlier: "Keep single docs and okf"), and "It's
weird that kmctl's README is so short, whereas kmaudit is longer. Why not
make top-level readme short and refer to the package READMEs".

Today the root `README.md` (387 lines) is kmctl's whole manual,
`packages/kmctl/README.md` is 11 lines pointing back at it,
`packages/kmaudit/README.md` is 199 lines, and kmaudit's command reference
sits in `packages/kmaudit/docs/commands.md` (466 lines), outside the root
`docs/` that `kmctl check` and `review due` look after.

After this ticket:

- The root `README.md` is short: what the repository is, the two packages
  with one line each linking to their READMEs, a link to `docs/`, and how
  to work on the repository (gates, the loop).
- `packages/kmctl/README.md` carries what the root README says about kmctl
  today: install, setup, the harness sections, upgrade and remove, why,
  quick start, what it does not do, and links into `docs/`.
- `packages/kmaudit/README.md` keeps its overview, install, harness setup,
  briefing and agents and skills sections, and links to the reference.
- `packages/kmaudit/docs/commands.md` moves (`git mv`) to
  `docs/reference/kmaudit-commands.md`, with the front matter
  `docs/` pages take (`.claude/rules/docs-layout.md`); `kmctl check --fix`
  rewrites `docs/reference/README.md`, and `packages/kmaudit/docs/` is gone.
- What reads those files follows: `scripts/release.py` (`DOC_FILES` pins
  kmctl's install lines in the root README today, and `KMAUDIT_DOCS` the
  tracing line), the release workflow's `git add` lists, the release skill,
  `docs/README.md`, the tests that read the root README, kmaudit's docs
  test in `test_mcp.py`, `.okf` pages that cite either file, and every link
  to an old path.

It worked when the root README is a short map whose links resolve, kmctl's
and kmaudit's READMEs each tell a user how to install and use that package,
kmaudit's reference lives under `docs/reference/` and passes `kmctl check`,
and `release.py set` still pins every install line in its new place.

## Problems

- P1: The root README is kmctl's manual while kmctl's own README is a stub, and kmaudit's reference lives outside the root docs/, so the repository's docs follow no single shape.

## Goals

- G1: One docs/ for the repository, a README per package for its users, and a root README that points at them.

## Outcomes

### O1: The root README maps the repository; each package README covers its package; kmaudit's reference lives in docs/reference
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `README.md`, `packages/kmctl/README.md`, `packages/kmaudit/README.md`, `packages/kmaudit/docs/commands.md`, `new:docs/reference/kmaudit-commands.md`, `docs/reference/README.md`, `docs/README.md`, `scripts/release.py`, `.github/workflows/release.yml`, `.claude/skills/release/SKILL.md`, `packages/kmctl/tests/*.py`, `packages/kmaudit/tests/*.py`, `tests/*.py`, `tests/scripts/*.py`, `.okf/architecture/overview.md`
- checked by: a test that the root README links both package READMEs and docs/ and stays under 80 lines; that packages/kmctl/README.md holds kmctl's install line, the apm.yml entry and the harness sections; that packages/kmaudit/docs/ is gone and docs/reference/kmaudit-commands.md documents every kmaudit MCP tool and command; `release.py set` and `set --package kmaudit` pin the install lines in their new files; `kmctl check` passes with the docs indexes regenerated; no link in README files, docs/ or .okf points at a moved path
- seen by: operator

## Could invalidate this plan

- none
