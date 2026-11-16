---
type: plan
title: 'Plan: kmctl-build-hook-to-config'
description: kmctl's hatch_build.py goes; a force-include table in its pyproject puts the APM package's skills, agents and rules in the wheel, now that apm/ sits inside packages/kmctl.
tags:
- plan
slug: kmctl-build-hook-to-config
epic: monorepo-release
depends_on:
- apm-per-package
schema_version: '2.0'
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T18:43:44+00:00'
---

# kmctl-build-hook-to-config

Relayed from: none

## Intent

The operator asked why kmaudit has no `hatch_build.py` and kmctl does, then
said to go ahead. kmctl's hook exists because its wheel needs copies of its
APM package's skills, agents and rules (`kmctl/_skills`, `_agents`,
`_rules`) for `kmctl briefing` and `kmctl plugin patch`, and the APM package
used to sit two folders up (`../../apm`) in a checkout but inside the
sdist. Since apm-per-package it is `packages/kmctl/apm` in both, so a
`[tool.hatch.build.targets.wheel.force-include]` table in
`packages/kmctl/pyproject.toml` maps the three folders directly. The hook,
its `apm-include` table and `scripts/check_wheel.py`'s reading of that table
go; `check_wheel.py` reads the force-include table instead. The hook also
skipped editable installs, so an editable kmctl reads `apm/` from the
checkout; the force-include table must keep that, or the change does not
ship. ADR 0044's and ADR 0045's lines about the hook follow.

It worked when both wheels build with no custom hook, kmctl's wheel holds
the same `_skills`, `_agents` and `_rules` files as before, and an editable
install still reads the checkout's `apm/`.

## Problems

- P1: kmctl carries a custom build hook whose only reason, a path outside the package folder, is gone.

## Goals

- G1: Both packages build with plain hatch configuration.

## Outcomes

### O1: kmctl's wheel gets its APM folders from a force-include table, with no build hook
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmctl/hatch_build.py`, `packages/kmctl/pyproject.toml`, `scripts/check_wheel.py`, `tests/scripts/test_check_wheel.py`, `tests/test_workspace_layout.py`, `.okf/decisions/0044-kmctl-and-kmaudit-are-both-workspace-packages.md`, `.okf/decisions/0045-each-package-keeps-its-apm-package-and-version.md`
- checked by: a test that packages/kmctl has no hatch_build.py and no custom hook table; the wheel build test checks kmctl's wheel holds the same _skills, _agents and _rules entries as the apm folders; check_wheel reads the force-include table and refuses a wheel missing an entry; a test that an editable install's site-packages holds no _skills, _agents or _rules
- seen by: operator

## Could invalidate this plan

- hatch's force-include may also copy the folders into an editable install, so an editable kmctl would read stale copies instead of the checkout's apm/. To be spiked by building both ways.
