---
type: decision
title: "ADR 0050: Drafts are settled before review, and only a person accepts one"
description: "kmctl decision accept makes a draft decision stable and logs who accepted it, and the CI action runs kmctl check --no-drafts on pull requests that are ready for review, so no draft reaches review."
tags: [decision]
generated:
  by: process:kmctl/0.15.0
  at: 2026-11-23T09:58:36Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/accept.py"
  - resource: "packages/kmctl/src/kmctl/checks.py"
  - resource: "action/knowledge-ci.sh"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0050: Drafts are settled before review, and only a person accepts one

## Context

ADR 0031 lets a decision record be `draft` until its choice is accepted, and
then its `status` becomes `stable` and a log line says so. Nothing made that
happen. `kmctl check` passes a draft, no verb accepts one, and the rule says
only that the status "becomes" stable, so an agent or a person edits the
front matter by hand, or nobody does.

In a repository where about ten people work on one bundle with coding
agents, 29 of the 44 decision records that merged pull requests added were
still `draft` when they merged. 20 of its 36 decisions were drafts on `main`.
Agents write most records there, so a draft that merges is a choice nobody
said yes to.

Verification did not fill the gap. `kmctl verify` asks a person to reread a
concept, and `kmctl review due` lists every concept nobody has verified. In
that repository it listed 48 pages, 24 of them decisions. A list that long is
read by nobody.

## Decision

The author of a pull request accepts or drops each draft before review, their
coding agent runs the command, and CI blocks a draft at review.

- **`kmctl decision accept NUMBER`** sets a draft's `status` to `stable`,
  changes no other line, and adds a line to `.okf/log.md` naming the person:
  `--by human:<id>`, or `human:` and git's `user.email` when `--by` is left
  out. It refuses a record that is not a draft, and a `--by` that is not a
  person. Accepting is a lifecycle event, so it gets a log line.
- **`kmctl check --no-drafts`** adds one error, check name `draft`, for each
  decision record whose `status` is `draft`, with the `accept` command that
  clears it. Without the flag, a draft passes, as before.
- **The CI action's new `drafts` input** decides when the check gets the flag.
  The default, `fail-when-ready`, sets it on a pull request that is ready for
  review, read from the event GitHub writes. A draft pull request and a push
  pass with drafts. `fail` sets it always, `pass` never. A workflow adds
  `ready_for_review` to its `pull_request` types so marking a pull request
  ready runs the check again.
- **The knowledge rules** gain the constraint
  `drafts-are-settled-before-review`. The coding agent writes a decision as a
  draft, lists the open drafts before the pull request goes ready, explains
  each one, and runs `kmctl decision accept` only on the author's explicit
  yes. To drop a draft, it deletes the file and its index line.
- **CI never accepts.** `stable` always means a person said yes.

Rejected:

- **Checking only the drafts a branch adds or changes.** That leaves the
  drafts already on `main` as they are. The repository that changes to this
  way of working accepts or drops them once instead.
- **Failing on drafts everywhere by default.** A draft pull request is where
  a draft belongs, so the default leaves it alone and checks at review.
- **Counting a pull request's approval as accepting its decisions.** An
  approval is about the whole change. It records no one's yes to a specific
  record.
- **`kmctl accept` at the top level.** kmctl's decision verbs live under
  `kmctl decision`, and `supersede` already takes a record's number.

## Consequences

- **A repository with drafts on `main` fails its first ready pull request
  after the upgrade.** Its people accept or drop each draft once. This
  repository has two, ADR 0041 and ADR 0042, and this record is a draft until
  a person accepts it.
- **`stable` means a person said yes, and the log says who.** The log line
  names the person; the record itself does not change beyond its `status`.
- **ADR 0031 holds, with a correction:** `kmctl check --no-drafts` fails a
  draft, and `kmctl decision accept` is how a draft becomes stable.
- **The rule's body changed,** so the okf-bundle hash in `OLD_RULES` in
  `packages/kmctl/tests/test_apm_package.py` moved, with its comment naming
  this record.
- **Whether a stable decision still holds is a separate question.** A scoped
  audit on each pull request, which reports and changes nothing, is the next
  step and needs its own decision, because ADR 0005 and ADR 0017 keep the
  audit off pull request code today.
