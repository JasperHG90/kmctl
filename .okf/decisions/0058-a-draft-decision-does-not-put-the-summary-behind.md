---
type: decision
title: "ADR 0058: A draft decision does not put the summary behind"
description: "A change to a decision that is a draft before and after it, including adding or deleting a draft, does not count as a concept change for the summary; accepting the draft still does."
tags: [decision]
generated:
  by: process:kmctl/0.17.1
  at: 2026-11-26T13:28:40Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/summary.py"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0058: A draft decision does not put the summary behind

## Context

The summary is behind when a concept changed in a commit that no edit of the
summary and no ack file has in its history
([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md),
[ADR 0048](0048-kmctl-summary-ack-writes-one-file-per-ack-so-branches-merge-without-a-conflict.md)).
A decision record is a concept, also while it is a draft
([ADR 0031](0031-a-decision-record-may-be-draft-until-it-is-accepted.md)). So `kmctl new decision`
puts the summary behind, and so does each edit of the draft after it. The
author runs `kmctl summary ack` for a choice that nobody has accepted yet, and
since [ADR 0056](0056-the-ci-action-fails-a-pull-request-whose-summary-is-behind.md)
CI fails a pull request that forgets that ack.

[ADR 0054](0054-a-verify-does-not-put-the-summary-behind.md) made a change
that touches only `verified` and `stale_after` no change for the summary. It
kept the accept of a draft as a change, because a summary can say that a
decision is a draft.

## Decision

This amends ADR 0054. The summary's freshness check also ignores a change to
a decision record that is a draft on both sides of the change. That covers a
draft that is added, a draft that is edited and stays a draft, and a draft
that is deleted. It compares each commit with its parent, and the working tree
with `HEAD`, as ADR 0054 does. A concept counts when any of its changes is not
ignored.

Accepting a draft still counts: the change from `draft` to `stable` puts the
summary behind. The summary is read once the choice is settled, and the
author updates it or acks then.

We rejected two other ways:

- **Keep counting drafts, because a summary can say that a decision is a
  draft.** A summary distils what the knowledge says as a whole. A draft is a
  choice that nobody has accepted, and [ADR 0050](0050-drafts-are-settled-before-review-and-only-a-person-accepts-one.md) settles every draft before
  review. A summary that names a draft is out of date as soon as the draft is
  accepted or dropped, and the accept already makes the summary behind.
- **Write an ack file with `kmctl new decision`.** An ack says the summary
  still holds. A command that writes a record does not read the summary, so
  that ack would claim something nobody checked.

## Consequences

- A pull request that adds a draft decision needs no ack until the draft is
  accepted.
- The accept still needs an ack or a summary edit. A pull request that adds a
  draft and accepts it before review still needs one.
- A draft that is dropped before review leaves the summary as it was.
- A decision that is changed back from `stable` to `draft` counts, because the
  change is not draft on both sides.
