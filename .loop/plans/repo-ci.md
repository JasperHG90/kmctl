---
type: plan
title: 'Plan: repo-ci'
description: A CI workflow for this repository that runs kmctl check, prek and pytest on every pull request.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:36:51+00:00'
slug: repo-ci
epic: null
depends_on: []
priority: null
---

# repo-ci

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

kmctl has no CI that tests a pull request: `.github/workflows/knowledge.yml`
only runs the action on this repository. Replace it with
`new:.github/workflows/ci.yml`, run on every pull request and every push to
main, with three jobs:

- `knowledge`: kmctl's own check on this repository, `uses: ./`, as
  `knowledge.yml` does today (checkout with full history for review due).
- `prek`: `uvx prek@0.5.5 run --all-files`, the hooks in
  `.pre-commit-config.yaml`, at the version `justfile` pins.
- `tests`: `uv run pytest`, the default suite. The integration tier stays
  in the loop's gate, which its marker description already says.

Actions are pinned by commit SHA with the version as a comment, as in
`.github/workflows/release-tag.yml`, and setup-uv runs with its cache off.
`new:tests/test_ci.py` reads the workflow and checks the triggers, the
three jobs and their commands, and that `knowledge.yml` is gone.

The outcome: a pull request to main runs kmctl check, prek and pytest.

## Could invalidate this plan

- The default test suite needs something a bare runner lacks (kmctl, agy,
  claude or APM on PATH, a git identity, files under HOME), so the tests
  job fails on GitHub. Holds: spike:repo-ci/1.
- prek's hooks fail or change files on a bare runner, so the prek job
  fails on a clean tree. Holds: spike:repo-ci/2.
