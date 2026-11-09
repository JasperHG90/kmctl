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
a package with `name: kmctl` and `virtual_path: apm` at that URL. APM 0.33.0
splits a git source over `host`, `port` and `repo_url` (owner/repo): spike
apm-only-install/6 locked `http://127.0.0.1:PORT/o/kmctl.git` as
`repo_url: o/kmctl`, `host: 127.0.0.1`, and spikes 4 and 5 show `port`. So
`LockDependency` gains `host` and `port`, the lock side is built as
`host[:port]/repo_url` (host `github.com` when absent), and the entry's URL
is compared after dropping its scheme, any user part, the `.git` suffix and
a trailing slash, case-insensitively. `write_manifest` replaces the first
such entry in place and removes the others, and install prints a note naming
each entry it replaced that had another source.

The reverse order (default source first, then another) must not reach `apm
uninstall`: `_names_old_package` today also matches kmctl's own
`{git: ...knowledge-management..., path: apm}` entry, and no spike shows
`apm uninstall` removes that form. So `_names_old_package` matches only the
forms ADR 0013 users wrote (a string entry, or a mapping without
`path: apm`), and kmctl's own mapping form is left to `write_manifest`.

Tests in `tests/test_plugin.py`, with lock fixtures in APM's real shape
(`repo_url` owner/repo plus `host` and `port`): a local-source install
followed by a default-source install leaves one kmctl entry and a note;
the reverse order does the same and runs no `apm uninstall`; an unrelated
`path: apm` package whose lock name is not kmctl is kept.

Done when those tests pass and the gates pass.

## Could invalidate this plan

- none
