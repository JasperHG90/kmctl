---
type: decision
title: "ADR 0001: A standalone kmctl CLI that installs its own plugin"
description: "kmctl is its own tool, not part of loop-harness; it is a Typer CLI that installs its plugin, and the plugin's skills are thin."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
decision_status: Accepted
decided_on: 2026-10-15
---

# ADR 0001: A standalone kmctl CLI that installs its own plugin

- Status: Accepted
- Date: 2026-10-15

## Context

The knowledge setup in loop-harness v2 (docs/ by Diataxis, an .okf/ bundle,
rules and skills) worked, and the operator wants it in every repository,
including ones that do not run the loop.

## Decision

- kmctl is a standalone package and repository.
- It follows loop-harness ADR 0008: a Typer CLI whose help is written for
  agents, that installs its own plugin from the same release, and whose
  skills route to CLI verbs instead of carrying logic.

Rejected:

- Build it into loopctl. Repositories that do not run the loop could not use it.
- A plugin with no CLI. The briefing, the bookkeeping verbs and the CI checks
  need code that runs the same in every harness and in CI.
