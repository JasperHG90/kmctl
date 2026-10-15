---
type: decision
title: "ADR 0008: /handoff and /continue use OKF handoff concepts"
description: "/handoff writes a handoff as a concept in .okf/handoffs/ and /continue lists the live ones and loads the ones the user picks, following memex's skills of the same name but storing in the repository."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
---

# ADR 0008: /handoff and /continue use OKF handoff concepts

- Status: Accepted
- Date: 2026-10-15

## Context

The operator's memex plugin has /handoff and /continue skills
(github.com/JasperHG90/memex, packages/claude-code-plugin/skills).
/handoff writes a technical summary of where the work stands: summary, where
it stands, next steps, key references. /continue lists recent handoffs as a
multi-select, loads the chosen ones, summarizes them together and asks what
to do next. memex stores them as notes in its own service.

kmctl already has a place for this: .okf/handoffs/, where each note carries a
stale_after date.

## Decision

- /handoff writes a concept in .okf/handoffs/ through kmctl, which fills the
  front matter (type, title, description, generated, a stale_after date) and
  the index entry. The agent writes the four sections.
- /continue asks kmctl for the live handoffs, newest first, offers them as a
  multi-select (3 per question plus a more option), loads the chosen ones,
  summarizes them together and asks what to do next. It never acts before
  the user answers.
- Expired handoffs show in kmctl review due, not in /continue.

Rejected:

- Store handoffs in memex. That ties kmctl to a service a repository may not
  run, and the handoff would not travel with the repository.
- Keep them outside the bundle (for example in a scratch folder). They would
  not be versioned or audited with the rest of the knowledge.

## Correction, 2026-10-15

The record had no Consequences section; this adds it.

### Consequences

- `kmctl new handoff` writes the front matter, a `stale_after` 14 days
  out and the index entry; `kmctl handoffs` lists the live ones, newest
  first, for /continue.
- Handoffs are committed with the repository, so they travel with it and
  any reader of the bundle sees them.
- Expired handoffs stay in the bundle and show in `kmctl review due` until
  someone removes them.
- Matching a second /handoff in one session to the first needed a key,
  which ADR 0009 adds.
