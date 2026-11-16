---
type: plan
title: 'Plan: package-direction'
description: A decision records which package a feature belongs in by the direction it works - kmctl from code and decisions toward docs/ and .okf/, kmaudit from docs and .okf/ toward code - and the root README and CLAUDE.md point to it.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T11:35:09+00:00'
slug: package-direction
epic: monorepo-release
depends_on: []
priority: null
schema_version: '2.0'
---

# package-direction

Relayed from: none

## Intent

The repository has two packages and no stated rule for which one a new
feature goes in. The operator settled it while placing a skill that scans
git history for missing decisions: kmctl starts from the code and the
decisions and works toward `docs/` and `.okf/` (keeping knowledge current
as the code changes), while kmaudit starts from `docs/` and `.okf/` and works
toward the code (checking that what the docs claim still holds). A feature
goes in the package whose direction it shares, so the history scan is
kmctl's.

A new decision, written with `kmctl new decision`, records the rule, the
operator's words, the history scan as the case that settled it, and the
rejected alternative of deciding per feature by convenience. The root
README's Packages list says each package's direction in one clause, and
`CLAUDE.md`'s routing table gains a row pointing to the decision for "which
package a feature belongs in". ADR 0043, which split kmaudit out, is linked
from the new decision; it is not changed.

It worked when the decision exists with its skeleton and index entry, the
root README names both directions, `CLAUDE.md` routes to the decision, and
`kmctl check` and strict OKF validation pass.

## Problems

- P1: Nothing records which package a new feature belongs in, so each placement is argued again.

## Goals

- G1: Anyone adding a feature can tell from the repository which package it goes in.

## Outcomes

### O1: A decision states the direction rule and the README and CLAUDE.md point to it
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:.okf/decisions/0046-kmctl-works-from-code-toward-knowledge-and-kmaudit-from-knowledge-toward-code.md`, `.okf/decisions/index.md`, `.okf/log.md`, `.okf/summary.md`, `README.md`, `CLAUDE.md`, `tests/test_readmes.py`
- checked by: a test that the decision exists, matches the decision schema, names both directions and links ADR 0043; that the root README's entries for kmctl and kmaudit name their directions and link the decision; and that CLAUDE.md's routing table links it; kmctl check and strict OKF validation
- seen by: operator

## Could invalidate this plan

- none
