---
type: plan
title: 'Plan: release-notes-pr-tickets'
description: A pull request that brought ticket merges in drafts one release-notes bullet per ticket, not one bullet for the whole pull request.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T06:42:58+00:00'
slug: release-notes-pr-tickets
epic: monorepo-release
depends_on: []
priority: null
schema_version: '2.0'
---

# release-notes-pr-tickets

Relayed from: none

## Intent

`scripts/release_notes.py` drafts one bullet per pull request merge, with the
pull request's title. When the pull request carried a whole integration
branch, as #53 carried `agent-audit` with dozens of ticket merges into the
v0.13.0 and kmaudit-v0.1.0 releases, the draft says one line and the notes
had to be rewritten by hand. The releases rule says to fix the script when a
draft misses changes it should list.

The script now reads the pull request's own first-parent line, the commits
it brought in that main did not have, the same way it already reads a sync.
When that line holds ticket merges (`Merge loop/SLUG: SUMMARY`), each becomes
its own bullet, plain commits on that line go under Other changes, and the
pull request's own bullet is left out. A pull request with no ticket merges
keeps its single bullet with its title. Release pull requests stay skipped.
The package filter applies to each commit as before. The module docstring
and ADR 0012's description of the script follow.

It worked when a test repository whose main takes in a branch of ticket
merges through a pull request merge drafts one bullet per ticket and none
for the pull request, and drafting v0.13.0 from this repository lists the
agent-audit tickets.

## Problems

- P1: A pull request merge that brought ticket merges in drafts as one bullet, hiding every change it carried.

## Goals

- G1: The drafted release notes list each change a release ships.

## Outcomes

### O1: A pull request that brought ticket merges in drafts one bullet per ticket
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `scripts/release_notes.py`, `tests/scripts/test_release_notes.py`, `.okf/decisions/0012-releases-come-from-ci.md`
- checked by: tests that a pull request holding ticket merges drafts each ticket and not the pull request, that its plain commits go under Other changes, that a pull request with no ticket merges keeps its title bullet, and that the kmaudit package filter still applies inside the pull request
- seen by: operator

## Could invalidate this plan

- none
