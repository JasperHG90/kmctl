---
type: plan
title: 'Plan: handoff-and-continue-skills-reviewer-f4'
description: Deferred hardening from handoff-and-continue-skills, reviewer finding f4 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev77+gbd4712cf8.d20261015
  at: '2026-10-15T11:40:12+00:00'
slug: handoff-and-continue-skills-reviewer-f4
status: draft
epic: plugin
depends_on: []
priority: null
---

# handoff-and-continue-skills-reviewer-f4

Relayed from: handoff-and-continue-skills, reviewer finding f4 in review round 1

## Intent

The update path skips the title check that create applies, so kmctl new handoff '!!!' --key K rewrites an existing handoff with title "!!!" and heading "# !!!", while the same title is refused on create. at src/kmctl/concepts.py:210.

## Could invalidate this plan

- none
