---
type: decision
title: "ADR 0054: A verify does not put the summary behind"
description: "The summary's freshness check ignores a change that touches only the fields kmctl verify writes."
tags: [decision]
generated:
  by: process:kmctl/0.16.1
  at: 2026-11-26T08:25:25Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/summary.py"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0054: A verify does not put the summary behind

## Context

The summary is behind when a concept changed in a commit that no edit of the
summary and no ack file has in its history
([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md),
[ADR 0048](0048-kmctl-summary-ack-writes-one-file-per-ack-so-branches-merge-without-a-conflict.md)).
`kmctl verify` changes a concept: it adds an entry to `verified`, and with
`--stale-after` it changes `stale_after`
([ADR 0023](0023-kmctl-verify-records-a-person-s-check.md)). So every verify
put the summary behind, although a person's check changes nothing the summary
says. In a repository that used kmctl, a reviewer verified 10 pages on one
pull request and then had to run `kmctl summary ack` a second time. In
another, verifying 20 decisions after accepting them did the same.

## Decision

The summary's freshness check ignores a change that touches only `verified`
and `stale_after`. It compares each commit that changed a concept with its
parent, and the working tree with `HEAD`, outside those two fields, as
`kmctl review due` already does for `edited after verification`
([ADR 0032](0032-kmctl-review-due-decides-by-commit-order.md)). A concept
counts when any of its changes touches something else. Accepting a draft
still counts, because a summary can say that a decision is a draft.

We rejected two other ways:

- **`kmctl verify` also writes an ack file.** An ack says the summary still
  holds. A verify does not read the summary, so it would claim something
  nobody checked.
- **Leave it, and ack after each verify.** That is the extra step people
  forget, and with
  [ADR 0056](0056-the-ci-action-fails-a-pull-request-whose-summary-is-behind.md)
  a forgotten ack fails CI.

## Consequences

- A pull request that only verifies pages needs no ack.
- The check reads each changed concept's version before and after each
  commit since the last ack, in one `git cat-file --batch` call. The git
  call that reads those versions moved to a small `history` module, which
  `kmctl review due` uses too.
- `VERIFY_FIELDS` and the comparison outside them now live in `verify.py`,
  next to the code that writes those fields.
