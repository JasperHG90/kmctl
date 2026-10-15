---
type: plan
title: 'Plan: adapt-copied-rules'
description: "The rules copied from loop-harness name loopctl, v1/v2, ADR numbers and paths that do not exist here; this ticket makes each one true for kmctl or removes it."
generated: {by: 'process:loopctl/2.0.1.dev1+g4552fe226.d20261015', at: '2026-10-15T05:10:24+00:00'}
slug: adapt-copied-rules
epic: foundations
depends_on: []
priority: 1
---

# adapt-copied-rules

Relayed from: none

## Intent

The rules in `.claude/rules/` were copied from loop-harness. The aim-managed ones (listed in `aim.toml`) are general and stay as they are. The others name `loopctl`, loop-harness ADRs, v1 and v2 history, the v2 build plan in `.okf/proposals/` and replay cases that kmctl does not have.

For each non-aim rule: keep it and rewrite the parts that name loop-harness so they hold for kmctl, or delete it when nothing in it applies (for example `data-management.md`, `schema-versioning.md` and `measure-before-ticketing.md` may not fit yet). Update `AGENTS.md` to drop the note that points at this ticket.

Done when no file under `.claude/rules/` outside the aim-managed set mentions `loopctl`, `loop_harness`, `loop-harness`, `v1`, `v2` or a path that does not exist here, checked by a grep.

## Could invalidate this plan

- none
