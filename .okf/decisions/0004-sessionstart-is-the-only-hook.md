---
type: decision
title: "ADR 0004: SessionStart is the only hook"
description: "The plugin's only hook relays the briefing at session start; the operator rejected a nudge after code edits, a reminder at Stop and a commit gate."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
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

## Correction, 2026-10-15

The record had no Consequences section; this adds it.

### Consequences

- The plugin has one hook, and it exits 0 even when `kmctl` is missing or
  fails (I1, `tests/test_plugin.py`).
- Nothing reminds the agent after a code edit; stale knowledge surfaces only
  at session start, in `kmctl review due`, and in CI.

## Amended, 2026-10-17

[ADR 0017](0017-kmctl-runs-okf-s-stop-check-for-antigravity.md): in
Antigravity kmctl's plugin folder also relays okf's opt-in Stop check,
because APM's copy cannot run there. kmctl's own hook is still SessionStart
only; the operator chose this, and I1 says so.
