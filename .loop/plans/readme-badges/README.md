---
type: plan
title: 'Plan: readme-badges'
description: The root README and both package READMEs open with badges for lifecycle, CI, latest release, licence and Python; kmaudit is marked beta in its README, its badge, its command reference and its package metadata.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T09:06:08+00:00'
slug: readme-badges
epic: monorepo-release
depends_on: []
priority: null
schema_version: '2.0'
---

# readme-badges

Relayed from: none

## Intent

The operator asked to note kmaudit as beta and to add badges to the root
README and both package READMEs about lifecycle, CI, release and the like.
Today no README carries a badge, and nothing says kmaudit's MCP tools,
store and CLI may still change.

Badges, from shields.io and GitHub's own workflow badge, link to what they
report:

- `README.md`: CI on `main` (`.github/workflows/ci.yml`), licence and
  Python version under the title; in the Packages list, each package's
  lifecycle badge and latest release badge beside its name.
- `packages/kmctl/README.md`: lifecycle stable, CI, latest kmctl release
  (tags `v*`), licence, Python.
- `packages/kmaudit/README.md`: lifecycle beta, CI, latest kmaudit release
  (tags `kmaudit-v*`), licence, Python.

kmaudit is marked beta in four places: its lifecycle badge, a sentence near
the top of its README saying its MCP tools, store format and CLI may change
between minor releases, the same sentence at the top of
`docs/reference/kmaudit-commands.md`, and the `Development Status :: 4 -
Beta` classifier in `packages/kmaudit/pyproject.toml`. kmctl gets
`Development Status :: 5 - Production/Stable` to match its stable badge.
The root README notes kmaudit as beta in its Packages entry.

It worked when every README opens with the badges above, each release badge
filters to its own package's tags, and kmaudit's README, command reference
and wheel metadata say beta.

## Problems

- P1: No README shows a package's lifecycle, CI state or latest release.
- P2: Nothing tells a user that kmaudit is beta and may change.

## Goals

- G1: A reader sees each package's state and latest release at a glance.

## Outcomes

### O1: Each README opens with lifecycle, CI, release, licence and Python badges
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `README.md`, `packages/kmctl/README.md`, `packages/kmaudit/README.md`, `tests/test_readmes.py`
- checked by: a test that each README carries the lifecycle, CI, release, licence and Python badges, that the CI badge points at ci.yml on main, and that each release badge filters to its own package's tag family
- seen by: operator

### O2: kmaudit is marked beta in its README, command reference and package metadata
- kind: behaviour
- goal: G1
- fixes: P2
- needs: none
- touches: `packages/kmaudit/README.md`, `docs/reference/kmaudit-commands.md`, `packages/kmaudit/pyproject.toml`, `packages/kmctl/pyproject.toml`, `README.md`, `tests/test_readmes.py`
- checked by: a test that kmaudit's README and command reference say beta, that its lifecycle badge says beta and kmctl's stable, that the root README's kmaudit entry says beta, and that the two pyprojects carry the matching Development Status classifiers
- seen by: operator

## Could invalidate this plan

- none
