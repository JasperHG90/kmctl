---
type: decision
title: "ADR 0052: The starter keeps an anchor comment below each kmctl ref so updates merge a project's additions"
description: "The starter's ci.yml and apm.yml put a comment line after the kmctl pin so copier update merges a project's own additions cleanly, and just upgrade stops when a conflict remains."
tags: [decision]
generated:
  by: process:kmctl/0.16.0
  at: 2026-11-24T14:40:36Z
status: stable
sources:
  - resource: "starter/apm.yml.jinja"
  - resource: "starter/.github/workflows/ci.yml.jinja"
  - resource: "starter/justfile.jinja"
---

# ADR 0052: The starter keeps an anchor comment below each kmctl ref so updates merge a project's additions

## Context

`just upgrade` runs `copier update`, which renders the template at the old
and the new `kmctl_ref` and merges the difference into the project's files
with git. Between two releases the only difference is the pin: the
`uses: JasperHG90/kmctl@...` step in `.github/workflows/ci.yml` and the
kmctl `ref:` in `apm.yml`. In both files the pin was the last line of its
block: the last line of `ci.yml`, and in `apm.yml` the line before
`targets:` when the adversarial reviewer is off.

A project that adds its own steps, jobs, APM dependencies or an `mcp:` block
puts them right there, below the pin. Git treats that insertion and the new
pin as touching changes, so the merge left conflict markers in both files
on every upgrade, even though nothing the project wrote overlaps the pin.
copier still exits 0 then, and the recipe went on to `just kmctl install`
over files full of markers. A consumer repository hit this on two upgrades
in a row (v0.14.0 and v0.16.0).

## Decision

Each pin in the starter is followed by comment lines that never change:
after the `uses:` step in `ci.yml`, and after the last templated APM
dependency in `apm.yml`. They say to add a project's own content below
them. Git then sees an unchanged line between the pin and the project's
additions, and the merge is clean. The justfile's `kmctl`, `install` and
`install-frozen` recipes depend on a `_merged` recipe that refuses while
git holds unmerged paths: it names them, says how to finish, and exits.
The guard sits there and not in `upgrade` because `just` has already read
the old justfile when `copier update` rewrites it; the `just kmctl
install` that `upgrade` runs reads the new one, so the guard holds even on
the upgrade that first brings it in.

Rejected:

- **`_skip_if_exists` for `ci.yml` and `apm.yml`, with `just upgrade`
  rewriting the pins by a pattern.** It never conflicts, but copier would
  stop bringing any other template change to those files, and each one
  would need a copier migration. Rewriting by a pattern also guesses at
  which `kmctl@` and `ref:` lines are kmctl's.
- **Only documenting where to add content.** The project still has to find
  the page, and the failure stays silent: the recipe goes on to the install
  over the conflicted files.

## Consequences

A project's own content below the anchors merges without a conflict, and
the new tests in `packages/kmctl/tests/test_starter.py` hold both files to
that. A project made from a template without the anchors conflicts once,
on the upgrade that brings them in; the install now stops there with the
files named instead of running over them. Whoever resolves it keeps their
content below the anchor, or the next upgrade conflicts again. Content
placed between a pin and its anchor still conflicts, as does a hand edit
to the pin's own line.