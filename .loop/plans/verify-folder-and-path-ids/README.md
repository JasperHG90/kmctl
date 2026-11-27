---
type: plan
title: 'Plan: verify-folder-and-path-ids'
description: kmctl verify takes a folder id and the file paths a shell glob gives, and a refusal names the form that works.
tags:
- plan
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-27T09:49:58+00:00'
slug: verify-folder-and-path-ids
epic: null
depends_on: []
priority: null
schema_version: '2.0'
---

# verify-folder-and-path-ids

Relayed from: none

## Intent

`kmctl verify` takes only exact ids. On 2026-11-27 the operator read the
decisions and ran `kmctl verify decisions` and then `kmctl verify decisions/*`.
Both were refused with a message that named neither fix. `kmctl review due`
listed 59 `decisions/` ids and 9 `prototypes/` ids at the time, so the
operator needed a shell pipeline to verify the 59.

After this ticket:

- A folder id verifies every page under that folder that `kmctl review due`
  tracks: `kmctl verify decisions` writes an entry to each of the 59
  decision records and skips the section index. The page set comes from
  the same functions `kmctl review due` uses (`_concepts` and `_docs_pages` in
  `packages/kmctl/src/kmctl/review_due.py`), so the two verbs cannot disagree
  on what a page is. Docs folders work the same way (`docs/how-to`).
- A path from the repository root works: .okf/decisions/0001-x.md reads as
  decisions/0001-x, so `kmctl verify .okf/decisions/0*` works from the
  repository root. A docs path with .md already works.
- An id that names a file `kmctl review due` never lists, such as
  `decisions/index` or `log`, is refused. Today `decisions/index` writes a
  `verified` entry into the index. The refusal names the folder form, so the
  shell glob `.okf/decisions/*` is refused with
  `give kmctl verify decisions`.
- A refused id that matches no file but where a folder of that name exists
  can no longer happen, because the folder form now covers it. Any other
  refusal, including an id with a glob character still in it, names the
  folder form and `kmctl review due`.
- `handoffs` as a folder is refused, as a single handoff already is.

ADR 0055 rejected `verify --base` because "it would record checks for pages
nobody named". A folder id is a name the person types, but it covers pages
they did not list one by one. That choice goes in a draft decision record,
`new:.okf/decisions/0059-kmctl-verify-takes-a-folder-id.md`, for the
operator to accept, with ADR 0055 getting a correction that points at it.

What shows it worked: in a test repository with three decisions, an index
and a log, `kmctl verify decisions --by human:a` exits 0 and writes three
entries and three log lines, and the index stays byte for byte as it was.

## Problems

- P1: `kmctl verify` has no way to name every page in a folder, so verifying a section of the bundle takes one id per page or a shell pipeline.
- P2: `kmctl verify` refuses the `.okf/`-prefixed paths a shell glob from the repository root gives.
- P3: `kmctl verify` accepts ids `kmctl review due` never lists, such as `decisions/index`, and writes into that file.
- P4: A refused id gets a message that names neither the folder form nor the path form.

## Goals

- G1: A person who has read a section verifies it in one short command, typed or globbed.
- G2: `kmctl verify` and `kmctl review due` agree on which files are pages.

## Outcomes

### O1: A folder id verifies every page under it that review due tracks
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmctl/src/kmctl/verify.py`, `packages/kmctl/src/kmctl/review_due.py`, `kmctl verify`
- checked by: tests in `packages/kmctl/tests/test_verify.py` that verify `decisions` and a docs folder in a temporary repository and check each page's entry and the untouched index
- seen by: operator

### O2: A repository-root path with .md reads as its id
- kind: behaviour
- goal: G1
- fixes: P2
- needs: none
- touches: `packages/kmctl/src/kmctl/verify.py`, `kmctl verify`
- checked by: a parametrized test in `packages/kmctl/tests/test_verify.py` passing a concept path under .okf with .md and a docs path with .md
- seen by: operator

### O3: An id for a file review due never lists is refused
- kind: behaviour
- goal: G2
- fixes: P3
- needs: O1
- touches: `packages/kmctl/src/kmctl/verify.py`, `kmctl verify`
- checked by: a parametrized test in `packages/kmctl/tests/test_verify.py` refusing decisions/index, the same as a .okf path with .md, log and handoffs, each writing nothing
- seen by: operator

### O4: Refusals name the folder form and the help shows it
- kind: behaviour
- goal: G1
- fixes: P4
- needs: O1, O2
- touches: `packages/kmctl/src/kmctl/verify.py`, `packages/kmctl/src/kmctl/__init__.py`, `docs/reference/commands.md`, `packages/kmctl/apm/claude/.apm/instructions/okf-bundle.instructions.md`, `packages/kmctl/apm/antigravity/.apm/instructions/okf-bundle.instructions.md`, `.claude/rules/okf-bundle.md`
- checked by: tests asserting the refusal text for `decisions/*` and `decisions/index`, and `packages/kmctl/tests/test_help.py` for the verb's help
- seen by: operator

### O5: A draft decision record states the folder form and ADR 0055 points at it
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `new:.okf/decisions/0059-kmctl-verify-takes-a-folder-id.md`, `.okf/decisions/0055-one-verify-for-the-pages-a-branch-made-due.md`, `.okf/decisions/index.md`
- checked by: `kmctl check` and strict OKF validation of `.okf/`
- seen by: operator

## Could invalidate this plan

- none
