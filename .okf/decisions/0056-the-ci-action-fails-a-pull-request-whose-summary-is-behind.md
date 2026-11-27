---
type: decision
title: "ADR 0056: The CI action fails a pull request whose summary is behind"
description: "kmctl's CI action runs kmctl check --summary-current by default, so a summary behind its concepts fails the job; summary: pass only warns."
tags: [decision]
generated:
  by: process:kmctl/0.16.1
  at: 2026-11-26T08:25:25Z
status: stable
sources:
  - resource: "action.yml"
  - resource: "action/knowledge-ci.sh"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
---

# ADR 0056: The CI action fails a pull request whose summary is behind

## Context

`kmctl check` warns when the summary is behind the concepts that changed
after it ([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md)).
The knowledge rules ask for the summary to be updated, or acked, in the same
change. A warning in CI passes, so a pull request could merge with the
summary behind, and the next pull request inherited the warning. The fix is
one command, `kmctl summary ack`, which an agent can run without a person.

## Decision

`kmctl check --summary-current` reports a summary that is behind as an
error, not a warning. kmctl's CI action passes that flag by default, through
a new input, `summary`. With `summary: fail`, the default, the job fails,
and the message says to update the summary or run `kmctl summary ack`. With
`summary: pass`, it only warns, as before. A local `kmctl check` and the
pre-commit hook still only warn, because a commit in progress has often not
acked yet.

We rejected two other ways:

- **Keep the warning, and add an input that turns the failure on.** Every
  repository would have to opt in to a check that any project that follows
  the rules passes already.
- **Fail only on a pull request that is ready for review, as `drafts` does.**
  Acking needs no person, so there is no reason to wait for review, and a
  draft pull request that fails tells the author early.

## Consequences

- A repository whose summary is behind on its default branch fails its next
  pull request until someone acks. The release notes say so, and how to keep
  the old behaviour with `summary: pass`.
- [ADR 0054](0054-a-verify-does-not-put-the-summary-behind.md) stops a
  verify from putting the summary behind, so verifying pages does not fail
  the job.
- The knowledge rules say the action fails such a pull request, so the
  okf-bundle hash in `OLD_RULES` moved with
  [ADR 0055](0055-one-verify-for-the-pages-a-branch-made-due.md).
