---
type: plan
title: 'Plan: release-notes-hermes-reviewer-f2'
description: Deferred hardening from release-notes-hermes, reviewer finding f2 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T22:10:49+00:00'
slug: release-notes-hermes-reviewer-f2
status: draft
epic: monorepo-release
depends_on: []
priority: null
schema_version: '2.0'
---

# release-notes-hermes-reviewer-f2

Relayed from: release-notes-hermes, reviewer finding f2 in review round 1

## Intent

Lines under What changed that are not bullets are never checked. A paragraph before the first bullet is ignored, and any later non-blank line is joined onto the bullet above it. So a reply can add an intro sentence or a made-up claim with no reference and still pass every check. Only the person merging would catch it. at scripts/hermes_release_notes.py:69.

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
