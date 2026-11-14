---
type: plan
title: 'Plan: kmaudit-briefing'
description: kmaudit briefing prints each namespace's audit state in a few lines, read-only, for a session-start hook.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:59:57+00:00'
slug: kmaudit-briefing
epic: kmaudit
depends_on:
- kmaudit-namespaces
priority: 1
schema_version: '2.0'
---

# kmaudit-briefing

Relayed from: none

## Intent

The operator wants a CLI-only `kmaudit briefing` that injects summary
statistics from an existing kmaudit database, the way `kmctl briefing`
feeds a session start. Today nothing summarises the audit: an agent has to
run `kmaudit claims todo`, whose refresh drops the claims of changed
sections, or `kmaudit checks list` per namespace.

`kmaudit briefing [PATH] [--json]` prints, for each namespace of the
repository (`listing` in `packages/kmaudit/src/kmaudit/namespaces.py`), its
sections and how many are pending extraction, its claims, its checks by
status (holds, drift, fails, weak, not measured, not run, reasons, stale
reasons) and its open feedback, then one line naming what to do next
(`/extract-claims FOLDER` while sections are pending, `/write-checks
FOLDER` while claims lack an answer, `kmaudit ui FOLDER` while drift or
feedback is open). It is read-only: it cuts the pages and compares keys
without refreshing, counting a section as extracted when its stored key is
its key or one of `previous_keys` (spike 1 found every section would read
as pending otherwise). It prints nothing and exits 0 when the repository
has no namespace, and on any error it prints one line saying the briefing
is unavailable and exits 0, so a hook never blocks a session. The README
says how to wire it into a SessionStart hook in Claude Code.

It lives in `new:packages/kmaudit/src/kmaudit/briefing.py`, with
`packages/kmaudit/src/kmaudit/cli.py` adding the verb.

It worked when, on a copy of this repository's store, `kmaudit briefing`
prints the `.okf` namespace's counts matching `kmaudit checks list` and the
store is unchanged afterwards.

## Problems

- P1: Nothing summarises a repository's audit state without running a verb that changes the store.
- P2: A session-start hook built on kmaudit would block or spam a session when there is no audit or an error.

## Goals

- G1: An agent starts a session knowing where the audit stands and what to do next.

## Outcomes

### O1: kmaudit briefing prints each namespace's state and the next step
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:packages/kmaudit/src/kmaudit/briefing.py`, `packages/kmaudit/src/kmaudit/cli.py`, `new:packages/kmaudit/tests/test_briefing.py`, `packages/kmaudit/docs/commands.md`
- checked by: a test that the briefing's counts per namespace match `claims list` and `checks list`, that pending sections are counted without changing the store (its bytes are equal before and after), and that a store keyed under a previous hash reads as up to date
- seen by: operator

### O2: The briefing never fails a session start
- kind: support
- goal: G1
- fixes: P2
- needs: O1
- touches: `packages/kmaudit/src/kmaudit/briefing.py`, `packages/kmaudit/README.md`
- checked by: tests that a repository with no namespace prints nothing and exits 0, and that a broken store prints one unavailable line and exits 0
- seen by: operator

## Could invalidate this plan

- The briefing may be too slow or too long for a session-start hook.
  spike:kmaudit-briefing/1 timed it on a copy of this repository's store:
  the first open (copying the old store) 0.51s, cutting 212 sections and
  comparing keys 0.03s, counting check statuses 0.06s; and it found the
  `previous_keys` trap the plan now covers.
