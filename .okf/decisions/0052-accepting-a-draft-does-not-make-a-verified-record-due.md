---
type: decision
title: "ADR 0052: Accepting a draft does not make a verified record due"
description: "kmctl review due does not count a decision record's status going from draft to stable as an edit after verification."
tags: [decision]
generated:
  by: process:kmctl/0.16.0
  at: 2026-11-24T17:06:53Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/review_due.py"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0052: Accepting a draft does not make a verified record due

## Context

`kmctl review due` lists a verified concept as `edited after verification`
when a commit after its verification commit changes it outside `verified`
and `stale_after`
([ADR 0032](0032-kmctl-review-due-decides-by-commit-order.md)).
`kmctl decision accept` changes one line of a draft record, its `status`,
from `draft` to `stable`
([ADR 0050](0050-drafts-are-settled-before-review-and-only-a-person-accepts-one.md)).
So accepting a draft that a person had already verified made it due again,
although nothing in it changed that a reviewer could check. In a repository
that upgraded to v0.16.0 and accepted its 20 draft records at once, 18 of
them had been verified and came back as due.

## Decision

In a decision record, `kmctl review due` does not count a `status` that went
from `draft` to `stable` as an edit. Any other change to `status`, such as
`stable` to `deprecated`, still counts, and so does any other edit made with
the accept. In any other concept, a change to `status` still counts:
`kmctl decision accept` writes only decision records, and a person who
changes a practice's `status` by hand may have changed what it claims.

We rejected three other ways:

- **`kmctl decision accept` also writes a `verified` entry.** Accepting a
  choice and checking a record against the code are two acts.
  [ADR 0023](0023-kmctl-verify-records-a-person-s-check.md) keeps `verified`
  for a person's check, and accept would write one the person never gave.
- **Leave it, and verify each record again after accepting it.** That asks
  people to verify text they had already checked, which teaches them to run
  `kmctl verify` without reading.
- **Ignore `status` entirely.** A record that becomes `deprecated` says
  something new, and a reader should look at it again.

## Consequences

- A verified draft stays verified when it is accepted. A draft that was
  never verified is still listed as `unverified`.
- To make this one exception, `kmctl review due` reads `type` and `status`
  from both versions of the record, through `field` as every other read
  does.
- The command reference says so under `kmctl review due` and
  `kmctl decision accept`.
