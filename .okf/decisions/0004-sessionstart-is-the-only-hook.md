---
type: decision
title: "ADR 0004: SessionStart is the only hook"
description: "The plugin's only hook relays the briefing at session start; the operator rejected a nudge after code edits, a reminder at Stop and a commit gate."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
decision_status: Accepted
decided_on: 2026-10-15
---

# ADR 0004: SessionStart is the only hook

- Status: Accepted
- Date: 2026-10-15

## Context

No hook can tell whether knowledge is still true. Candidates were: the
briefing at SessionStart, a nudge after each code edit naming the concepts
that describe that file, a reminder at Stop when covered code changed, and a
gate that refuses a commit until those concepts are verified.

## Decision

Only SessionStart, relaying the briefing (ADR 0002), including what is due
for review. It never blocks.

Rejected by the operator:

- PostToolUse nudge after code edits.
- Stop reminder.
- Commit gate. A refactor changes code without making a page wrong, so it
  would refuse often for nothing.
