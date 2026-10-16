---
type: plan
title: 'Plan: apm-only-install-reviewer-f2'
description: Deferred hardening from apm-only-install, reviewer finding f2 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-16T21:15:08+00:00'
slug: apm-only-install-reviewer-f2
epic: multi-harness
depends_on: []
priority: null
---

# apm-only-install-reviewer-f2

Relayed from: apm-only-install, reviewer finding f2 in review round 1

## Intent

`write_manifest` (`src/kmctl/plugin.py`) replaces an earlier kmctl entry
only when its `git:` URL equals the current `--source`, and
`remove_old_apm_entry` only catches entries naming
jasperhg90/knowledge-management. So an install with a fork or a local
`--source` (as the integration tests and anyone trying an unreleased tree
do), followed by an install with the default source, leaves two kmctl
packages in apm.yml, with no note. APM then installs both, and the second
overwrites the first's files.

Measured: of the 2 install routes that take `--source`, both hit this when
the source changes between runs; the r9 integration test installs from a
local server, so every developer who later installs from GitHub in the same
scratch repo would see it.

Change: an apm.yml entry is kmctl's when it is a mapping with
`path: apm` and either its `git:` equals the current source, or names
jasperhg90/knowledge-management, or the repository's apm.lock.yaml records
the package at that URL with `name: kmctl` (URLs compared without scheme,
`.git` suffix, trailing slash or case). `write_manifest` replaces the first
such entry in place and removes the others, and install prints a note naming
each entry it replaced that had another source. Tests in
`tests/test_plugin.py`: an entry from a local source, recorded in the lock as
kmctl, followed by a default-source install, leaves one kmctl entry and a
note; an unrelated `path: apm` package whose lock name is not kmctl is kept.

Done when those tests pass and the gates pass.

## Could invalidate this plan

- none
