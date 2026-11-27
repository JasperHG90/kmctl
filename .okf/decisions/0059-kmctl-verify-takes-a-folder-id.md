---
type: decision
title: "ADR 0059: kmctl verify takes a folder id"
description: "kmctl verify takes a folder, such as decisions, for every page under it that review due lists, and a repository-root path with .md, so a person who read a whole section verifies it in one short command."
tags: [decision]
generated:
  by: claude-opus/5.5
  at: 2026-11-27T09:56:49Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/verify.py"
  - resource: "packages/kmctl/src/kmctl/pages.py"
---

# ADR 0059: kmctl verify takes a folder id

## Context

On 2026-11-27 the operator had read this repository's decision records and
wanted to record that. `kmctl review due` listed 59 `decisions/` ids. They
ran `kmctl verify decisions` and then `kmctl verify decisions/*`, and both
were refused with "no concept or docs page", which named neither way out. The
glob could not work from the repository root: it matched nothing, and
`.okf/decisions/*` gives `.okf/`-prefixed paths that verify refused. They
needed a shell pipeline over `kmctl review due` to verify the 59.

[ADR 0055](0055-one-verify-for-the-pages-a-branch-made-due.md) rejected
`kmctl verify --base origin/main` because "it would record checks for pages
nobody named". It also showed that `kmctl verify decisions/index` wrote a
`verified` entry into the section index, a file `kmctl review due` never lists.

## Decision

- `kmctl verify FOLDER --by human:<id>` verifies every page under the folder
  that `kmctl review due` lists: `decisions`, `prototypes`, `docs/how-to`.
  It leaves out the folder's index and any handoff, and the `handoffs`
  folder is refused. Both verbs read the page set from `kmctl.pages`, so
  they cannot disagree on what a page is.
- A path from the repository root with `.md` names the same page as its id:
  `.okf/decisions/0001-x.md` is `decisions/0001-x`. A shell glob such as
  `.okf/decisions/005*` works.
- An id for a file `kmctl review due` never lists, such as
  `decisions/index`, is refused. So is a glob that picks up an `index.md`,
  and the refusal names the folder form.
- A refusal for an id that names no page names the folder form for the
  nearest folder above it, so `kmctl verify decisions/*` is told to give
  `kmctl verify decisions`.

This does not undo ADR 0055's rejection. `--base` picks pages by what a
branch changed, which the person never typed. A folder is a name the person
types for pages they read, the same claim as listing each id. The help and
the knowledge rules say to give a folder only when the person read every page
in it.

We rejected two other ways:

- **Only make the refusal name the pipeline**
  (`kmctl review due | awk ... | xargs kmctl verify`). It leaves a shell
  pipeline as the way to do a common job, and an agent on another shell
  gets it wrong.
- **Let a folder id verify only the pages in it that are due.** Then
  `kmctl verify decisions` means something different from day to day, and a
  person who read the whole folder gets entries on some pages but not others.

## Consequences

- A person who read a section verifies it with one short command, and a
  shell glob from the repository root works.
- A folder verify writes an entry on every page in it, including pages
  that were not due. Each extra entry is a true record of a check.
- The knowledge rules name the folder form, so the okf-bundle hash in
  `OLD_RULES` in `packages/kmctl/tests/test_apm_package.py` moved, with its
  comment naming this record.
