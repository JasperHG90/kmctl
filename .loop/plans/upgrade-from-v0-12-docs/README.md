---
type: plan
title: 'Plan: upgrade-from-v0-12-docs'
description: kmctl's README and the APM how-to give the full path from v0.12.x to a later release, CLI first, and point auditing at kmaudit.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T19:44:43+00:00'
slug: upgrade-from-v0-12-docs
epic: monorepo-release
depends_on: []
priority: 1
schema_version: '2.0'
---

# upgrade-from-v0-12-docs

Relayed from: none

## Intent

The operator asked for the migration path for users, then: "Ok do it."
Released users are on v0.12.2 or older; none of the audit work was ever
released. Moving to the first release after the move (v0.13.0) takes, in
order: install the new CLI first (a kmctl at v0.12.2 or older cannot run a
pin to a later release, because it looks for kmctl at the repository root,
ADR 0044); change the `apm.yml` entry from `path: apm` to
`path: packages/kmctl/apm` with the new ref (`kmctl doctor` prints the exact
entry); run `apm install` and `kmctl plugin patch`. A starter project does
it with `just upgrade vX.Y.Z`. The action (`uses:`) and the pre-commit hook
(`rev:`) change only their tag. Auditing a folder of docs is now kmaudit's,
installed apart.

Today kmctl's README Upgrade section gets the order wrong: it says to
install a newer CLI "only for its own fixes", which fails for this move.
`docs/how-to/install-kmctl-with-apm.md` mentions the path change but not
the order. This ticket rewrites kmctl's README Upgrade section with the
steps above, adds an "Upgrade from v0.12" part to the how-to, and adds one
line in kmctl's README pointing at kmaudit's README for auditing. The v0.13.0
release notes get an "Upgrading from v0.12" section in the version pull
request itself, where `.claude/rules/releases.md` says notes are edited, so
this ticket does not touch the notes template.

It worked when a user on v0.12.2 can follow kmctl's README or the how-to and
end with the new CLI, the moved entry and a passing `kmctl doctor`.

## Problems

- P1: kmctl's README tells v0.12 users to upgrade the CLI only for its own fixes, which breaks the move to the next release, and no doc says auditing moved to kmaudit.

## Goals

- G1: A v0.12 user can upgrade by following the docs alone.

## Outcomes

### O1: kmctl's README and the APM how-to give the v0.12 upgrade steps in order and point auditing at kmaudit
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmctl/README.md`, `docs/how-to/install-kmctl-with-apm.md`, `packages/kmctl/tests/test_docs.py`
- checked by: a docs test that kmctl's README Upgrade section and the how-to say to install the new CLI before moving the pin past v0.12.2, give the path change, name `just upgrade` and `kmctl doctor`, and that kmctl's README links kmaudit's README
- seen by: operator

## Could invalidate this plan

- none
