---
type: plan
title: 'Plan: adr-kmaudit-stale-lines'
description: ADR 0012 gets a correction saying each package's version now lives in its APM package's apm.yml and release-tag watches those two files, since its 2026-11-14 correction still names packages/kmaudit/VERSION and apm/apm.yml.
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

ADR 0012's correction of 2026-11-14 says kmctl's version source is
apm/apm.yml (gone), kmaudit's is packages/kmaudit/VERSION (gone), and `release-tag.yml`
runs on a change to either. ADR 0045 moved kmctl's APM package to
`packages/kmctl/apm`, gave kmaudit `packages/kmaudit/apm/apm.yml` in place of
the VERSION file, and `release-tag.yml` now watches those two files, but ADR
0012 never says so: a reader of the release decision gets two paths that do
not exist. ADR 0012 gets a dated correction naming the two version sources
and the two watched paths, linking ADR 0045. Earlier sections stay as the
record of what was true then, as the repo's other corrections do.

It worked when ADR 0012's last correction names
`packages/kmctl/apm/apm.yml` and `packages/kmaudit/apm/apm.yml` as the
version sources and release-tag's paths, links ADR 0045, and the bundle
validates.

## Problems

- P1: ADR 0012's latest word on version sources names apm/apm.yml (gone) and packages/kmaudit/VERSION (gone), which no longer exist.

## Goals

- G1: The release decision describes the release flow as it is.

## Outcomes

### O1: ADR 0012 records where each package's version lives since ADR 0045
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `.okf/decisions/0012-releases-come-from-ci.md`
- checked by: a test that ADR 0012's last correction names both apm.yml version sources and links ADR 0045, and that every path in release-tag.yml's paths filter is named in it; strict OKF validation
- seen by: operator

## Could invalidate this plan

- none
