---
type: plan
title: 'Plan: ci-toiminnot'
description: Run ci.yml's prek and tests jobs through the operator's toiminnot actions instead of inline commands.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:57:46+00:00'
slug: ci-toiminnot
epic: null
depends_on: []
priority: null
---

# ci-toiminnot

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none
<!-- When this ticket carries a finding raised while building another ticket,
replace "none" with that ticket's slug and the finding, in one line (ADR 0001). -->

## Intent

The operator keeps reusable actions in https://github.com/JasperHG90/toiminnot
and wants `.github/workflows/ci.yml` to use them. Its `prek` and `tests` jobs
change to:

- `prek`: setup-uv (cache off), then
  `JasperHG90/toiminnot/actions/pre_commit` with `prek_version: "0.5.5"`
  (the version `justfile` pins) and `python_version: "3.12"`. In v1.3.0
  the names of two actions are swapped: `actions/pre_commit` runs prek and
  `actions/prek` runs pre-commit, so this uses `actions/pre_commit`, and a
  comment in `ci.yml` says why. A toiminnot release that fixes the swap
  changes what runs on a SHA bump, and the test catches it only through the
  `prek_version` input. The action installs no uv, while this repository's
  hooks call `uv run`, so uv goes on PATH first.
- `tests`: `JasperHG90/toiminnot/actions/pytest` with `directory: tests`,
  `markers: not integration` and `python_version: "3.12"`. Its empty
  default becomes `-m ""`, which would also run the integration tier.

Both pin v1.3.0 by its commit SHA with the tag as a comment, as the other
actions in `ci.yml` are pinned. Each action checks out the repository
itself, so those jobs drop their own checkout. The `knowledge` job keeps
`uses: ./`. `tests/test_ci.py` changes to check the two actions, their
inputs and the pins in place of the inline commands. The toiminnot
actions pin their own inner actions by tag and cache prek's and uv's
files; that is the operator's to change in toiminnot. The toiminnot pytest
action turns setup-uv's cache on inside itself; this repository cannot
change that, and the release workflows' cache is the release-cache-off
ticket's.

The outcome: a pull request runs kmctl check, and prek and pytest through
the toiminnot actions.

## Could invalidate this plan

- toiminnot's hook action cannot run this repository's hooks on a runner.
  Holds with uv on PATH: prek 0.5.5 through `actions/pre_commit`,
  spike:ci-toiminnot/3 (pre-commit 4.2.0 through `actions/prek` also
  passes, spike:ci-toiminnot/1).
- toiminnot's pytest action fails on this repository or runs the
  integration tier. Holds with `markers: not integration`:
  spike:ci-toiminnot/2.
