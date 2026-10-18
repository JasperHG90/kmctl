---
type: decision
title: "ADR 0025: The starter template lives in kmctl and shares its release tags"
description: "copier.yml sits at kmctl's root with the template in starter/, so each kmctl release tag is a template release, and scripts/release.py set moves kmctl_ref's default to it."
tags: [adr, decision, release, starter]
generated:
  by: process:kmctl/0.5.1
  at: 2026-10-18T10:10:12Z
status: stable
sources:
  - resource: "copier.yml"
  - resource: "scripts/release.py"
  - resource: "tests/test_starter.py"
---

# ADR 0025: The starter template lives in kmctl and shares its release tags

## Context

kmctl-starter, the copier template that sets up a new repository with kmctl,
lived in its own repository, JasperHG90/kmctl-starter. Copier takes a
template's versions from the tags of the repository it lives in, so the
template and kmctl had separate tags, and every kmctl release needed a
starter commit to move `kmctl_ref`'s default to it. Measured over the
starter's history (2026-10-18): 5 of its 10 commits only moved that pin, and
2 more followed a kmctl change and needed a kmctl ticket of their own. Its
CI failed 6 of its last 9 test runs, because the runner could not fetch
kmctl, which is private, so its bootstrap check was turned off.

The operator asked (2026-10-18) to fold the template into kmctl and to bump
the kmctl version in copier at each release, and said the two repositories
are always both public or both private.

## Decision

`copier.yml` sits at kmctl's root with `_subdirectory: starter`; the
template's files are in `starter/`. Copier cannot point at a subfolder of a
repository, so the root is the only place for it (spike:starter-in-repo/1).
A kmctl release tag is the template's release tag too, and
`uvx copier copy gh:JasperHG90/kmctl` renders from the newest one.

`scripts/release.py set` writes `kmctl_ref`'s default in `copier.yml` as
`vVERSION`, next to the apm.yml versions and the docs' install lines, and
the release workflow stages it, so the version pull request and the tag
on its merge carry a template that pins its own release. kmctl-starter's
daily bump workflow is gone: nothing is left for it to do. `kmctl_ref`'s
validator takes an a, b or rc suffix, since a pre-release writes one.

`kmctl_ref` stays a question. `just upgrade vX.Y.Z` runs `copier update
--data kmctl_ref=vX.Y.Z`: the template moves to the newest release and the
pin to the one named, older or newer. Tying the template to the pin with
`--vcs-ref` would break moving to an older release, because copier refuses
a downgrade and tags before the move have no template.

`tests/test_starter.py` renders the template from this tree for each
harness set, and its integration test runs `just bootstrap` in a generated
project with git rewriting kmctl's GitHub URL to a `file://` clone of this
tree, so the CLI and the package come from the checkout. APM 0.33.0 follows
a rewrite to `file://` but refuses one to `http://` or another host
(spike:starter-in-repo/5, /4). CI's starter job runs it.

## Consequences

- A generated project sees a new template version at every kmctl release,
  even when the template did not change; `copier update` then changes
  only `_commit` in `.copier-answers.yml`, a one-line change to commit.
- Tags before the first release with the template (v0.5.1 and older) have
  no template, so copier cannot render from them.
- A project made from kmctl-starter records a `_src_path` naming
  that repository and a `_commit` from it. It moves
  once: point `_src_path` at gh:JasperHG90/kmctl and run `copier recopy`,
  which replaces the files the template writes. A plain `copier update`
  leaves conflicts, because kmctl has its own v0.3.0 tag
  (spike:starter-in-repo/2). The how-to gives the steps.
- The starter is exactly as public as kmctl. The operator accepted that.
- kmctl-starter is archived, with its README pointing here.
