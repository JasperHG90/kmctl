---
type: plan
title: 'Plan: write-docs-skill-reviewer-f3'
description: Deferred hardening from write-docs-skill, reviewer finding f3 in review round 2.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev47+g2444f9291.d20261015
  at: '2026-10-15T11:29:06+00:00'
slug: write-docs-skill-reviewer-f3
status: draft
epic: plugin
depends_on: []
priority: null
---

# write-docs-skill-reviewer-f3

Relayed from: write-docs-skill, reviewer finding f3 in review round 2

## Intent

grade.py maps run folders to type folders by hard-coded eval names (tutorial-getting-started, howto-supersede, ...) that evals.json never records, so a fresh skill-creator run with other folder names stops with a KeyError at plugin/skills/write-docs/evals/grade.py:16.

## Could invalidate this plan

- none
