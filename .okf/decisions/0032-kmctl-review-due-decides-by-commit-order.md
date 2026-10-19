---
type: decision
title: "ADR 0032: kmctl review due decides by commit order"
description: "kmctl review due finds the commit that holds a file's newest verified entry and compares sources and the file itself with HEAD from there, so a squash or rebase merge keeps a verification and an edit after it makes the file due."
tags: [decision]
generated:
  by: process:kmctl/0.10.0
  at: 2026-10-19T15:16:46Z
status: stable
---

# ADR 0032: kmctl review due decides by commit order

- Status: Accepted
- Date: 2026-10-19

## Context

`kmctl review due` compared a source's last committer date with the newest
`verified[].at`, the UTC time `kmctl verify` writes
([ADR 0023](0023-kmctl-verify-records-a-person-s-check.md)). A squash or
rebase merge writes new commits dated at merge time, so a concept verified on
a branch was `source changed` again once the branch landed (issue #17). And
nothing compared the concept's own text with what the person verified, so an
edit after a verification was never a reason (issue #18).

The summary already decides by commit order, not dates
([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md)).
A loop spike (`review-due-commit-order/2`) checked the rule below in 33
cases (squash, rebase and merge-commit landings, issue #18's edit, re-verify
with and without `--stale-after`, docs pages) and timed it on this
repository.

## Decision

- A concept or docs page's **verification commit** is the oldest commit in
  its history whose front matter holds its newest `verified[].at` in the
  working tree. A squash or rebase carries the entry into the new commit, so
  the verification commit moves with it. While that entry is not committed,
  nothing counts as changed after it.
- **Source changed**: a source differs between the verification commit and
  `HEAD` (`git diff --quiet V HEAD -- SOURCE`). A docs page without
  `verified` uses its own last commit as the baseline, also by commit.
- **Edited after verification**, a new reason: the file differs between the
  verification commit and `HEAD` in its body or in any front matter field
  other than `verified` and `stale_after`, the two `kmctl verify` writes.
- One `git log --cc --name-only` over every verified file and one
  `git cat-file --batch` find all the verification commits. `--cc` lists a
  merge whose result differs from every parent, as a `git log` of the file
  alone does.
- The `--json` shape does not change; the new reason is one more string in
  `reasons`.

Rejected:

- Record a hash of each source in the `verified` entry. It would also catch a
  change made after the verification inside one squashed commit, but it
  needs a field outside OKF v0.2
  ([ADR 0006](0006-staleness-from-okf-fields.md), invariant I4).
- One `git log` per verified file. The spike timed it at 1.765 s for this
  repository's 40 concepts and docs pages, against 0.359 s for the batched
  walk.

## Consequences

- A verification made on a branch survives a squash, rebase or merge commit
  landing.
- An edit to a verified file, in its body or another front matter field,
  lists it again until a person verifies it again.
- Commit order cannot see order inside one commit: a branch that verifies a
  concept and then changes its source, squashed into one commit, loses that
  change.
- The batched walk and a per-file `git log` can pick different commits when
  the same change reached both sides of a merge (a cherry-pick) and the merge
  took the other side's tree. Both commits hold the entry; only the baseline
  for `source changed` differs.
- A source edited but not committed still counts only once it is committed,
  as ADR 0023 says.
