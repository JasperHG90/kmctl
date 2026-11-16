---
type: plan
title: 'Plan: adr-kmaudit-stale-lines'
description: ADRs 0001, 0012 and 0014 get corrections, and the decisions index its notes, saying each package's version and APM package now live under packages/<name>/apm (ADR 0045), since they still name apm/apm.yml and packages/kmaudit/VERSION.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T06:43:00+00:00'
slug: adr-kmaudit-stale-lines
epic: monorepo-release
depends_on: []
priority: null
schema_version: '2.0'
---

# adr-kmaudit-stale-lines

Relayed from: none

## Intent

ADR 0045 moved kmctl's APM package from apm/ (gone) to `packages/kmctl/apm`
and gave kmaudit `packages/kmaudit/apm/apm.yml` in place of
packages/kmaudit/VERSION (gone); `release-tag.yml` now watches those two
apm.yml files. Several decisions still give the old paths as their latest
word, with no correction pointing at ADR 0045:

- ADR 0012's 2026-11-14 correction names apm/apm.yml (gone) and
  packages/kmaudit/VERSION (gone) as the version sources and release-tag's
  trigger.
- ADR 0001 says apm/apm.yml (gone) carries the release version.
- ADR 0014 says kmctl's package is apm/ (gone) and its `version:` is the one
  version source.
- `.okf/decisions/index.md` notes ADR 0012 as "apm/apm.yml is the one
  version source" and ADR 0014 as shipping "the APM package in apm/".

Each of ADRs 0001, 0012 and 0014 gets a dated correction naming the paths as
they are and linking ADR 0045; the index notes for 0012 and 0014 follow.
Earlier sections stay as the record of what was true then, as the repo's
other corrections do. ADR 0013 is superseded by ADR 0014 and stays as it is.

It worked when each of the three ADRs has a correction that names
`packages/kmctl/apm/apm.yml` and links ADR 0045, ADR 0012's names both
apm.yml files and every path release-tag watches, the two index notes no
longer name the old paths, and the bundle validates.

## Problems

- P1: ADRs 0001, 0012 and 0014 and the decisions index give apm/apm.yml and packages/kmaudit/VERSION, which no longer exist, as the latest version sources and package path.

## Goals

- G1: The decisions describe where each package's version and APM package live today.

## Outcomes

### O1: ADRs 0001, 0012 and 0014 and the index record the package paths since ADR 0045
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `.okf/decisions/0001-standalone-cli-installs-its-plugin.md`, `.okf/decisions/0012-releases-come-from-ci.md`, `.okf/decisions/0014-apm-is-the-only-install-route.md`, `.okf/decisions/index.md`, `tests/scripts/test_release_docs.py`
- checked by: tests that each of the three ADRs has a correction naming packages/kmctl/apm/apm.yml and linking ADR 0045, that ADR 0012's names both apm.yml files and every path in release-tag.yml's paths filter, and that the index notes for 0012 and 0014 name no old path; strict OKF validation
- seen by: operator

## Could invalidate this plan

- none
