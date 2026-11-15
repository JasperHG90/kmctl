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
priority: 2
schema_version: '2.0'
---

# release-notes-hermes-reviewer-f2

Relayed from: release-notes-hermes, reviewer finding f2 in review round 1

## Intent

Fix: a non-blank line under What changed that is not a `- ` bullet and is not
indented under one fails a new `stray-line` check, unless the draft's What
changed has the same line (the draft's own "None."). Lines under What changed that are not bullets are never checked. A paragraph before the first bullet is ignored, and any later non-blank line is joined onto the bullet above it. So a reply can add an intro sentence or a made-up claim with no reference and still pass every check. Only the person merging would catch it. at scripts/hermes_release_notes.py:69.

## Problems

- P1: A line under What changed that is not a bullet or an indented continuation of one is never checked, so a rewrite can add an intro or an unreferenced claim and still be kept.

## Goals

- G1: Every line Hermes adds under What changed carries one of the draft's references, or the draft stands.

## Outcomes

### O1: The cleaning script falls back to the draft when a stray line appears under What changed
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `scripts/hermes_release_notes.py`, `tests/scripts/test_hermes_release_notes.py`
- checked by: tests that a rewrite with a paragraph before the first bullet, or an unindented line after a bullet, falls back to the draft with a warning naming the check; an indented continuation line is still joined and kept; a draft whose What changed holds a non-bullet line (such as "None.") passes when the rewrite keeps that line
- seen by: operator

## Could invalidate this plan

- The check may throw away good rewrites. spike:release-notes-hermes-reviewer-f2/1 measured it on the 15 real rewrites from spike:release-notes-hermes/1: none had a stray line, so it would have dropped none. On benign drafts it changes nothing; it guards the crafted-subject case of ADR 0035, which benign history cannot show.
