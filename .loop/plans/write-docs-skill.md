---
type: plan
title: 'Plan: write-docs-skill'
description: "One skill for writing docs/ pages by Diataxis type, with a reference file per type."
slug: write-docs-skill
epic: plugin
depends_on: [claude-plugin]
priority: 9
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:23+00:00'
---

# write-docs-skill

Relayed from: none

## Intent

Adds a `write-docs` skill to the plugin: it picks the Diataxis type from what the reader is trying to do (learn, do one task, look something up, understand why), and has one reference file per type with what belongs and what does not. It updates the `docs/` index page (`README.md`) in the same change.

One skill rather than four, so there is one trigger to get right.

Done when the skill, given four requests of different types, puts each page in the right folder.

Every skill is made with the skill-creator skill (ADR 0007), and its test prompts are kept beside it.

## Could invalidate this plan

- none
