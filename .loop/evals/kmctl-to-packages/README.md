---
type: eval
title: 'Eval: kmctl-to-packages'
description: 'Definition of done for kmctl-to-packages: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T19:49:06+00:00'
slug: kmctl-to-packages
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: d066b171f65c36a13ac67b5c116964040d129613f746f975a04e8dc749474d0f
  at: '2026-11-14T19:49:06+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The root pyproject.toml is a virtual uv workspace root ([tool.uv] package = false, members packages/*, both members workspace sources in the dev group) and kmctl's own pyproject.toml lives in packages/kmctl.
  Fails when: the root declares an installable package, a member is missing from the workspace or dev group, or src/kmctl still exists at the root
- r2: `uv build --package kmctl` (wheel built from the sdist) and `uv build --wheel --package kmctl` each give a wheel at apm/apm.yml's version holding _skills, _agents and _rules that scripts/check_wheel.py and scripts/smoke_wheel.py accept.
  Fails when: either build fails, a wheel's version differs from apm/apm.yml, a folder is missing, or check_wheel or smoke_wheel refuses it
- r3: One root `uv run pytest -m 'not integration'` collects the root tests/, packages/kmctl/tests and packages/kmaudit/tests with no collection error, and they pass.
  Fails when: a collection error, a tree collects nothing, or a test fails
- r4: The pin hand-off adds #subdirectory=packages/kmctl only for refs newer than v0.12.1, for the command and the not-installed notice; the starter renders kmctl_src the same way.
  Fails when: a ref at or below v0.12.1 gets the fragment, or a newer ref lacks it
- r5: Every install line and hint (README, docs, hooks.json, HOOK_INSTALL, release-notes template, action.yml) installs kmctl from packages/kmctl, and `scripts/release.py set` keeps the fragment.
  Fails when: any install line for a post-move release lacks #subdirectory=packages/kmctl, action.yml installs from the root, or release.py set drops the fragment
- r6: No .okf source, docs page or local rule cites src/kmctl or the old root tests path, and ADR 0044 records the move.
  Fails when: kmctl check or the strict OKF validation fails, a cited path does not exist, or there is no ADR 0044
