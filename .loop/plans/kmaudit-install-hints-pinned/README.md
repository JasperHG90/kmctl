---
type: plan
title: 'Plan: kmaudit-install-hints-pinned'
description: A kmaudit release pins every install hint kmaudit prints or documents, not only the README line.
tags:
- plan
slug: kmaudit-install-hints-pinned
epic: monorepo-release
status: draft
depends_on:
- release-per-package
schema_version: '2.0'
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T21:35:07+00:00'
---

# kmaudit-install-hints-pinned

Relayed from: release-per-package, reviewer round 1 note (out-of-scope gap)

## Intent

`scripts/release.py set --package kmaudit` pins only kmaudit's README
install line to `@kmaudit-vX.Y.Z#subdirectory=packages/kmaudit`. The other
hints stay unpinned, so a released kmaudit tells users to install from
main: `INSTALL` in `packages/kmaudit/src/kmaudit/steps.py` and
`packages/kmaudit/src/kmaudit/judge.py`, and the `kmaudit[tracing]` line in
`packages/kmaudit/docs/commands.md`. `set` should pin each of them, refuse
when one is missing, and the Release run's kmaudit bump should stage them.
A fix round built this once and reverted it, because no finding of that
ticket asked for it.

## Problems

- P1: A kmaudit release leaves the install hints in its code and docs pointing at main.

## Goals

- G1: Every kmaudit install hint names the release it ships in.

## Outcomes

### O1: set --package kmaudit pins every kmaudit install hint
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `scripts/release.py`, `.github/workflows/release.yml`, `tests/scripts/test_release.py`
- checked by: a test that `set --package kmaudit` pins the README, steps.py, judge.py and docs/commands.md lines, and refuses when one is missing
- seen by: operator

## Could invalidate this plan

none
