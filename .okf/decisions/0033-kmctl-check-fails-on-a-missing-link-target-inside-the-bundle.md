---
type: decision
title: "ADR 0033: kmctl check fails on a missing link target inside the bundle"
description: "kmctl check reports every link in .okf/ whose target does not exist, relative or from the bundle root, as it does for docs/, instead of leaving links inside the bundle to the okf validator, which only warns."
tags: [decision]
generated:
  by: process:kmctl/0.11.0
  at: 2026-10-19T19:43:01Z
status: stable
sources:
  - resource: "src/kmctl/checks.py"
---

# ADR 0033: kmctl check fails on a missing link target inside the bundle

- Status: Accepted
- Date: 2026-10-19

## Context

`kmctl check` failed on a missing link target in `docs/` and on an `.okf/`
link that leaves the bundle, but skipped every link that stays inside
`.okf/`: relative links that resolve inside it and `/` links, which OKF
resolves from the bundle root (section 6.1). Those were left to the okf
validator, and the validator only warns about a missing target, even with
`--strict`, because OKF lets a bundle travel without every concept.

So a link to a concept that was renamed or deleted passed `kmctl check` and
CI stayed green. It happened while renumbering a decision log in a project
that uses kmctl (issue #32): every link to an old number broke and no check
failed.

## Decision

- `kmctl check` reports a link anywhere in `.okf/` whose target does not
  exist, with the same `link` finding it gives for `docs/`: a relative link
  from the page's folder, and a `/` link from the bundle root.
- An index entry's own link is left to the index check, which already
  reports an entry with no file, so a missing concept is reported once. This
  covers `.okf/index.md` and each section's `index.md`, as `docs/README.md`
  is covered today. Every other link on an index line is still checked.
- Links that leave the bundle are checked as before.

Rejected:

- Leave links inside the bundle to the okf validator and make a project run
  it with warnings as errors. The validator's warning is right for a bundle
  that travels on its own, and kmctl does not own the validator. In a
  repository kmctl manages, every concept is in the same tree, so a missing
  target is a mistake, and `kmctl check` is the check that already runs in
  the pre-commit hook and the CI action.

## Consequences

- Renaming or deleting a concept fails `kmctl check` until every link to it
  is fixed, in `.okf/` as in `docs/`.
- A project that upgrades kmctl may see new `link` errors for links that
  were already broken.
- A `/` link in `.okf/` written to mean the repository root, as GitHub
  renders it, now fails unless the bundle holds that path. OKF reads it from
  the bundle root, so the fix is a relative link.
- `log.md` is checked like any page. kmctl's own verbs name concepts there in
  backticks, not links, and the okf-bundle rule asks the same of hand-written
  lines, so an append-only log rarely holds a link that can break.
- The okf validator still warns about the same links; the two checks now
  agree on what is broken, and only kmctl fails on it.
