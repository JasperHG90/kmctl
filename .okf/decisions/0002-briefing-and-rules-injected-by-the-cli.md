---
type: decision
title: "ADR 0002: The CLI injects the briefing and the rules into context"
description: "kmctl serves one briefing that combines state (what is due for review), routing (where knowledge lives) and the rules for writing it, and the harness hook relays it."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
---

# ADR 0002: The CLI injects the briefing and the rules into context

- Status: Accepted
- Date: 2026-10-15

## Context

Rules as files (.claude/rules/) load only in harnesses that support them,
and each harness has its own format and path scoping. A docs page about how
to manage knowledge is read only if the agent goes looking for it.

## Decision

kmctl prints one briefing that combines:

- state: what is due for review, live handoffs;
- routing: where each kind of knowledge lives and which skill to use;
- the rules for writing knowledge.

The plugin's SessionStart hook relays it. Every harness that can run a
command at session start can inject it, so this is the one method that
works across harnesses.

Rejected:

- Native rule files per harness. Only some harnesses have them, and each
  needs its own format.
- A docs page. An agent reads it only if it already knows to look.

## Correction, 2026-10-15

The record had no Consequences section; this adds it.

### Consequences

- `kmctl briefing` is the one source; the SessionStart hook only prints
  it, so upgrading the CLI updates the briefing in every repository.
- It must fit a word budget (I3, 600 words, tested), so every new line in it
  costs space.
- The rules it carries ship inside the package (`src/kmctl/rules/`), not as
  harness rule files.
- The skills it names are read from the packaged plugin's `skills/` folder
  at run time, so a new skill shows up without editing the briefing.
