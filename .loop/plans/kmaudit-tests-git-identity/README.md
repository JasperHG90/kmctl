---
type: plan
title: 'Plan: kmaudit-tests-git-identity'
description: kmaudit's test git helper commits with its own identity, so the kmaudit CI job passes on a runner with no git config.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T20:52:49+00:00'
slug: kmaudit-tests-git-identity
epic: monorepo-release
depends_on: []
priority: 1
schema_version: '2.0'
---

# kmaudit-tests-git-identity

Relayed from: none

## Intent

Pull request #53's CI failed in the kmaudit job: tests that commit on top
of the fixture repository call `git(root, "commit", ...)` from
`packages/kmaudit/tests/fixtures/audit_repo.py`, which passes no identity,
and a fresh GitHub runner has no git user, so git exits 128. Locally the
operator's global git config hides it. Reproduced here with
`GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1`: 1 failure and 14
errors in packages/kmaudit/tests.

The helper passes `-c user.name=t -c user.email=t@example.com` on every
call, as `make_repo` already does for its own commit, so every caller gets
an identity. The eval runs kmaudit's tests with no global or system git
config, so the gate catches it from now on.

It worked when packages/kmaudit/tests pass with `GIT_CONFIG_GLOBAL=/dev/null`
and the kmaudit CI job on #53 goes green.

## Problems

- P1: kmaudit's tests commit without a git identity, so they fail on any machine with no git user, CI's runner included.

## Goals

- G1: kmaudit's tests pass on a machine with no git config.

## Outcomes

### O1: kmaudit's test git helper always commits with its own identity
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmaudit/tests/fixtures/audit_repo.py`
- checked by: packages/kmaudit/tests run with GIT_CONFIG_GLOBAL=/dev/null and GIT_CONFIG_NOSYSTEM=1 and pass
- seen by: operator

## Could invalidate this plan

- none
