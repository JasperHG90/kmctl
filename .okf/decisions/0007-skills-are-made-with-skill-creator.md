---
type: decision
title: "ADR 0007: Every skill is made with the skill-creator skill"
description: "Each skill in the plugin is drafted, tested on realistic prompts and tuned with Claude's skill-creator skill, not written by hand."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
---

# ADR 0007: Every skill is made with the skill-creator skill

- Status: Accepted
- Date: 2026-10-15

## Context

A skill fires only when its description matches what a user asks, and does
the right thing only if its body was tried on real requests. A hand-written
SKILL.md is usually checked by reading it once.

## Decision

The operator requires every skill in kmctl's plugin to be made with the
skill-creator skill (anthropic-skills:skill-creator): draft, run it on
realistic prompts, and tune the description for triggering. A ticket that
adds or changes a skill says so in its plan and keeps the test prompts it
used.

Rejected:

- Hand-written skills reviewed by reading. Nobody sees a description that
  never triggers until a user hits it.

## Consequences

- Skill tickets take longer, and the reviewer can check the prompts the
  skill was tested on.
