---
type: plan
title: 'Plan: action-pin-shas'
description: Pin the composite action's inner actions, and knowledge-audit.yml's, to commit SHAs and test the pins.
tags:
- plan
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:29:37+00:00'
slug: action-pin-shas
epic: null
depends_on: []
priority: null
---

# action-pin-shas

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

Pin every `uses:` in the composite action `action.yml` to a full 40-character
commit SHA with its version as a trailing comment, so a workflow that pins
`JasperHG90/kmctl@<SHA>` pins everything the action runs (issue #19). The three
lines are `action.yml:136` (`astral-sh/setup-uv@v6`), `:192`
(`actions/upload-artifact@v4`) and `:200` (`actions/download-artifact@v4`).

Pin to the releases the repo's own workflows already run, so one version of
each action is in use across the repo:

- `astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0`
  (as in `.github/workflows/ci.yml`)
- `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2`
  (as in `.github/workflows/release.yml`)
- `actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2`
  (latest release; nothing in the repo pins it yet)

The same reason applies to `.github/workflows/knowledge-audit.yml`, the one
repo workflow still on tags (`actions/checkout@v4`, `astral-sh/setup-uv@v6`,
`actions/upload-artifact@v4`, `actions/download-artifact@v4`). It runs a model
with an API key, and `ci.yml`, `release.yml` and `release-tag.yml` are already
pinned, so pin it the same way (checkout at
`3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`, as in `ci.yml`).

Keep the pins enforced the way the repo already does it: add `action.yml` and
`knowledge-audit.yml` to the parametrize list of
`test_every_action_is_pinned_by_commit_sha` in `tests/scripts/test_workflows.py`,
which checks each `uses:` line for `@<40 hex> # vX.Y.Z`. Today it covers only
the two release workflows; `ci.yml` has its own check in `tests/test_ci.py`.

Out of scope: `starter/.github/workflows/ci.yml.jinja` and the examples in
`docs/how-to/install-the-plugin-and-the-ci-action.md` keep readable tags on
purpose (the doc says so), and adding Dependabot to bump pins is a separate
choice the issue does not ask for.

Outcome: `just test` passes with `action.yml` and `knowledge-audit.yml` in the
pin test, and `grep -n "uses:" action.yml` shows only SHA pins with version
comments.

## Could invalidate this plan

- none
