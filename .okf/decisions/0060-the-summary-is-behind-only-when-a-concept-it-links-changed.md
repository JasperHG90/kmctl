---
type: decision
title: "ADR 0060: The summary is behind only when a concept it links changed"
description: "The summary freshness check counts a changed concept only when the summary links to it; a change to any other concept needs no ack."
tags: [decision]
generated:
  by: process:kmctl/0.18.0
  at: 2026-11-27T09:55:14Z
status: draft
sources:
  - resource: "packages/kmctl/src/kmctl/summary.py"
  - resource: "packages/kmctl/src/kmctl/review_due.py"
---

# ADR 0060: The summary is behind only when a concept it links changed

## Context

The summary is behind when a concept changed in a commit that no edit of the
summary and no ack file has in its history
([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md),
[ADR 0048](0048-kmctl-summary-ack-writes-one-file-per-ack-so-branches-merge-without-a-conflict.md)).
Every concept counts, except a change to `verified` or `stale_after` only
([ADR 0054](0054-a-verify-does-not-put-the-summary-behind.md)) and a change to
a draft decision ([ADR 0058](0058-a-draft-decision-does-not-put-the-summary-behind.md)).
Since [ADR 0056](0056-the-ci-action-fails-a-pull-request-whose-summary-is-behind.md),
the CI action fails a pull request while the summary is behind, so each such
change costs a `kmctl summary ack` or an edit of the summary.

The summary cites the concepts it rests on as links. A concept it does not
link cannot make one of its sentences wrong. Yet a change to such a concept
puts the summary behind as much as a change to one it cites.

We counted the merges on `main` since 2026-10-01: the first-parent commits
that changed a concept, each checked against the links in the summary of
that commit.

- In this repository the summary links 27 of 71 concepts. 41 of the 72
  merges that changed a concept changed only concepts the summary does not
  link. 8 of the 10 ack files acked only such concepts.
- In a repository that used kmctl, the summary links 44 of 71 concepts. 12
  of the 70 merges that changed a concept changed only concepts it does not
  link. 3 of its 4 ack files acked only such concepts.

## Decision

A changed concept puts the summary behind only when the summary links to
it. The links are the Markdown links in the body of `.okf/summary.md` in the
working tree that resolve to a concept's file. A change to any other concept
is no change for the summary, whether that concept is edited, added or
deleted. The exceptions of ADR 0054 and ADR 0058 still apply to the concepts
the summary links. `kmctl review due` lists the summary with the same
concepts, and `--base` keeps it only when the branch changed one of them.

Rejected:

- **Keep counting every concept**, because a new concept may be one the
  summary should mention. The ack does not check that either: an agent runs
  `kmctl summary ack` for a concept the summary never cited, and in 8 of 10
  acks in this repository that is all an ack covered. Whether the summary
  covers what it should is a question for an audit of the whole bundle, not
  for each pull request.
- **Count a new concept, but not an edit of one the summary does not link.**
  Most new concepts are draft decisions, which ADR 0058 already skips, or
  pages too detailed for a 500-word summary. Counting new concepts would
  keep most of the acks this record removes.
- **Make a summary that is behind a warning again, in CI as well.** That
  reverses ADR 0056 for every concept, also for one the summary cites and
  may now state wrongly. This record keeps the check and makes it fire only
  when a sentence of the summary can be wrong.

## Consequences

- A pull request that changes only concepts the summary does not link needs
  no ack. In this repository that was 41 of 72 merges, in the other 12 of 70.
- A summary that links more concepts gets fewer of these savings. A team
  can link only the concepts it rests on.
- Removing a link from the summary is an edit of the summary, so it covers
  the concept the link pointed to.
- A new concept that the summary should mention is no longer flagged by the
  freshness check. An audit of the bundle has to find it.
- ADR 0027's rule that the summary is behind when a concept changed gets a
  correction that points here when this is built.
- Nothing is built until this record is accepted.
