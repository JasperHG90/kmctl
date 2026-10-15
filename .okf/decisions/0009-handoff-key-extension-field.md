---
type: decision
title: "ADR 0009: handoff_key is kmctl's one OKF extension field"
description: "A handoff carries handoff_key, the Claude Code session id, so a second /handoff in one session updates the same concept; it is the only extension field kmctl writes, and invariant I4 now allows fields an ADR names."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision, okf, handoffs]
status: stable
decision_status: Accepted
decided_on: 2026-10-15
---

# ADR 0009: handoff_key is kmctl's one OKF extension field

- Status: Accepted
- Date: 2026-10-15

## Context

`/handoff` run twice in one session should update one handoff, not add a
second (ADR 0008). That needs a key kmctl can match. The Claude Code session
id is available to the skill as `CLAUDE_CODE_SESSION_ID`. OKF v0.2 has no
field for it. Invariant I4 said kmctl uses only spec fields, and the
operator had said OKF extensions are fine as long as they stay few.

## Decision

- A handoff written by kmctl carries `handoff_key` in its front matter: the
  session id it was written in.
- I4 now reads: kmctl uses the spec's fields plus the extension fields an ADR
  names. `handoff_key` is the only one.

Rejected:

- Match on title. Two handoffs in one session with different titles would
  not be found, and two sessions with the same title would collide.
- Put the key in the file name. File names name an entity, and a session id
  in every name makes the section index unreadable.

## Consequences

- The okf validator accepts unknown keys, so bundles stay conformant.
- Adding any other extension field needs its own ADR.
