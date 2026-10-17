---
type: plan
title: 'Plan: release-cache-off'
description: Turn setup-uv's cache off in the release workflows, so a cache entry written by the audit agent's job can never reach a release build.
tags:
- plan
slug: release-cache-off
status: draft
epic: null
depends_on: []
priority: null
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T08:02:48+00:00'
---

# release-cache-off

Relayed from: agent-publish, plan round 3 note: `.github/workflows/release.yml` and `release-tag.yml` set setup-uv `enable-cache: true`.

## Intent

The audit agent (ADR 0017) runs shell commands as the runner's user, with
passwordless sudo on GitHub-hosted runners, so it could read the job's
runtime token and write Actions cache entries on `main`. The release
workflows restore setup-uv's cache before they build and publish the wheel,
so a poisoned entry could end up in a release. Set `enable-cache: false` on
every setup-uv in `.github/workflows/release.yml` and
`.github/workflows/release-tag.yml`, with a test that checks it, and note
the reason in ADR 0012 or ADR 0017.

The outcome: no workflow that builds or publishes a release restores a
cache.

## Could invalidate this plan

- none
