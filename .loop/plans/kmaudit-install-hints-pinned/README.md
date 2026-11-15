---
type: plan
title: 'Plan: kmaudit-install-hints-pinned'
description: A kmaudit release pins every install hint kmaudit prints or documents, not only the README line.
tags:
- plan
slug: kmaudit-install-hints-pinned
epic: monorepo-release
status: draft
priority: 2
depends_on:
- release-per-package
- apm-per-package
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
`packages/kmaudit/src/kmaudit/judge.py` (both used in refusal messages by
`check_verbs.py`, `judge.py` and `ui.py`), and the `kmaudit[tracing]` line
in `packages/kmaudit/docs/commands.md`. One of those messages is also
wrong: `judge.py` tells a user whose `LANGSMITH_TRACING=true` lacks
langsmith to reinstall with `INSTALL`, which has no `[tracing]` extra, so
following it leaves the error in place.

The two code hints stop being hand-written strings. One function in
kmaudit builds the install line from kmaudit's own installed version, the
way kmctl's hook hint does: a release version names its tag
(`@kmaudit-vX.Y.Z#subdirectory=packages/kmaudit`), a dev or local version
names no ref, and it takes the extras, so the tracing message asks for
`kmaudit[tracing]`. `steps.py` and `judge.py` use it, so nothing in the code
needs pinning at release. `set --package kmaudit` pins the README line and
the docs' tracing line, and refuses, writing nothing, when either is
missing; the Release run's kmaudit bump stages both. A fix round built
part of this once and reverted it, because no finding of that ticket asked
for it.

It worked when an installed kmaudit at a release version prints install
hints naming its tag, the tracing hint names the extra, and a kmaudit
release pins both docs lines.

## Problems

- P1: A kmaudit release leaves the install hints in its code and docs pointing at main, and the tracing hint leaves out the extra it needs.

## Goals

- G1: Every kmaudit install hint names the release it ships in, with the extras it needs.

## Outcomes

### O1: kmaudit's code builds its install hint from its version, and set --package kmaudit pins the docs' hints
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmaudit/src/kmaudit/steps.py`, `packages/kmaudit/src/kmaudit/judge.py`, `packages/kmaudit/src/kmaudit/check_verbs.py`, `packages/kmaudit/src/kmaudit/ui.py`, `packages/kmaudit/docs/commands.md`, `packages/kmaudit/tests/test_judge.py`, `scripts/release.py`, `.github/workflows/release.yml`, `tests/scripts/test_release.py`, `tests/scripts/test_workflows.py`
- checked by: tests that the install hint names `kmaudit-v0.2.0` for version 0.2.0, no ref for 0.2.0.dev1, and `kmaudit[tracing]` in the tracing refusal; that `set --package kmaudit` pins the README and the docs' tracing line and refuses when one is missing; and that the release workflow stages docs/commands.md in a kmaudit bump
- seen by: operator

## Could invalidate this plan

- none
