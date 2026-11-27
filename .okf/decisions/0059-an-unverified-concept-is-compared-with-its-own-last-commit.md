---
type: decision
title: "ADR 0059: An unverified concept is compared with its own last commit"
description: "kmctl review due compares the sources of a concept with no verified entry against the concept's own last commit, as it does for a docs page, so a branch that changes them lists it."
tags: [decision]
generated:
  by: claude-opus/5.5
  at: 2026-11-26T16:20:56Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/review_due.py"
---

# ADR 0059: An unverified concept is compared with its own last commit

## Context

`kmctl review due` lists a concept as `source changed` when a commit after
its verification commit changes one of its sources
([ADR 0032](0032-kmctl-review-due-decides-by-commit-order.md)). A concept with
no `verified` entry has no verification commit, so its sources are never
compared. It is listed only as `unverified`.

With `--base`, a page the branch did not edit keeps only its `source changed`
reasons ([ADR 0055](0055-one-verify-for-the-pages-a-branch-made-due.md)).
So a pull request that changes the code of a never-verified concept does not
list that concept, and the person who changed the code is never told to
read it.

A `docs/` page without `verified` already avoids this: its sources are
compared with the page's own last commit
([ADR 0022](0022-docs-pages-carry-optional-okf-front-matter-and-generated-folder-indexes.md)).
Today a team gets the same for a concept only by running `kmctl verify` on
every new concept. When that verify is run only to give the concept a
baseline, its `human:` entry claims a check that nobody made.

## Decision

A concept with no `verified` entry uses its own last commit as the baseline
for `source changed`, by commit order, as a `docs/` page does. It keeps the
`unverified` reason. `edited after verification` still needs a verification
commit, so a never-verified concept never gets that reason.

We rejected two other ways:

- **Keep the gap, and tell teams to verify every new concept.** That makes
  `kmctl verify` bookkeeping for the history check instead of a record of a
  person's check ([ADR 0023](0023-kmctl-verify-records-a-person-s-check.md)).
- **Use the concept's first commit as the baseline.** A later edit of the
  concept usually updates it for the code that changed before that edit, so
  it would be listed again for a change it already covers. The page's own
  last commit is also the rule a `docs/` page follows.

## Consequences

- `kmctl review due --base` lists a never-verified concept when the branch
  changes one of its sources, with the reason `source changed: SOURCE`.
- In the full list, such a concept can carry `source changed` next to
  `unverified`.
- A team can leave `kmctl verify` out of its pull requests and still see,
  in every pull request, the concepts whose code changed.
