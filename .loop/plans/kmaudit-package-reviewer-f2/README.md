---
type: plan
title: 'Plan: kmaudit-package-reviewer-f2'
description: Deferred hardening from kmaudit-package, reviewer finding f2 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T12:45:21+00:00'
slug: kmaudit-package-reviewer-f2
status: draft
epic: kmaudit
depends_on: []
priority: null
schema_version: '2.0'
---

# kmaudit-package-reviewer-f2

Relayed from: kmaudit-package, reviewer finding f2 in review round 1

## Intent

PREVIOUS_HASHES carries a store keyed under the old full-text hash over to whatever GUIDANCE hashes to today. If a later ticket changes GUIDANCE and leaves the tuple alone, a store last refreshed before this change keeps answers extracted under the old guidance. Nothing tells the next editor to empty it, and no test fails if they forget. at packages/kmaudit/src/kmaudit/instructions.py:132.

## Problems

<!-- One line per problem this ticket fixes: - P1: text. Every problem is
fixed by at least one outcome. -->

- P1: The problem this ticket fixes, in one line.

## Goals

<!-- One line per goal the fixes serve: - G1: text. Every goal is served by
at least one outcome. -->

- G1: What fixing it serves, in one line.

## Outcomes

<!-- One block per outcome: a heading ### O1: what changes, then exactly these
one-line bullets. kind: behaviour (stands alone), support (serves another
outcome) or follow-up. goal: a G id. fixes: a P id. needs: none, or the O ids
it needs first, comma-separated. touches: the paths, CLI verbs or keys it
changes, each in backticks, comma-separated (new: marks a file it creates).
checked by: the test or check that shows it. seen by: operator, calling code
or nobody. loopctl plan lint writes these to .loop/plans/SLUG/facts.json. -->

### O1: What changes, in one line
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `loopctl verb`
- checked by: the test that shows it works
- seen by: operator

## Could invalidate this plan

- none
