---
type: plan
title: 'Plan: kmaudit-namespaces-nested-store'
description: kmaudit namespaces and briefing open a nested namespace's store, whose file name holds %2F, instead of failing with unable to open database file.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:02:02+00:00'
slug: kmaudit-namespaces-nested-store
epic: kmaudit
depends_on: []
priority: 1
schema_version: '2.0'
---

# kmaudit-namespaces-nested-store

Relayed from: none

## Intent

The operator ran `kmaudit namespaces` in this repository and got
`sqlite3.OperationalError: unable to open database file` from
`namespaces._count`. The repository has two stores, .kmaudit/.okf.sqlite
and .kmaudit/packages%2Fkmaudit.sqlite: a nested namespace's file name
quotes its `/` as `%2F` (`namespaces.store_file`). `_count` opens the store
read-only as `sqlite3.connect(f"file:{store}?mode=ro", uri=True)`, and
SQLite decodes `%2F` in a URI back to `/`, so it looks for
.kmaudit/packages/kmaudit.sqlite, which does not exist. Every namespace
below the top level fails this way, and so does any repository path with
`%`, `?` or `#` in it. `briefing.py` opens its stores the same way, and
`store.py` opens the legacy store the same way when it copies it.

The fix is one helper in `packages/kmaudit/src/kmaudit/namespaces.py` that
gives a store's read-only URI from `Path.as_uri()`, which percent-encodes
`%`, `?` and `#`, and the three call sites use it. A store that cannot be
opened at all still raises, since that is a real fault, but a missing table
stays a count of 0 as today.

It worked when `kmaudit namespaces` and `kmaudit briefing` list a nested
namespace's counts in a repository whose store file name holds `%2F`.

## Problems

- P1: kmaudit namespaces and kmaudit briefing fail with "unable to open database file" whenever a repository has a nested namespace, because the read-only SQLite URI decodes the %2F in its file name.

## Goals

- G1: Every namespace kmaudit stores can be listed and briefed.

## Outcomes

### O1: Read-only store URIs are built from Path.as_uri, so nested namespaces open
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmaudit/src/kmaudit/namespaces.py`, `packages/kmaudit/src/kmaudit/briefing.py`, `packages/kmaudit/src/kmaudit/store.py`, `packages/kmaudit/tests/test_namespaces.py`, `packages/kmaudit/tests/test_briefing.py`, `packages/kmaudit/tests/test_claims_store.py`
- checked by: tests that run `kmaudit namespaces --json` and `kmaudit briefing` in a git repository with a store for `handbook/guides` holding a section, which must list its counts; and that the legacy store copy works from a repository path holding `%` and `#`
- seen by: operator

## Could invalidate this plan

- none
