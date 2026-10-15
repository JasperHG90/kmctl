---
type: decision
title: "ADR 0006: Staleness comes from OKF's own fields; a covers field is out of scope"
description: "kmctl decides what is due for review from stale_after, verified and sources, which OKF v0.2 already defines; a field mapping concepts to code paths is deferred."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
decision_status: Accepted
decided_on: 2026-10-15
---

# ADR 0006: Staleness comes from OKF's own fields; a covers field is out of scope

- Status: Accepted
- Date: 2026-10-15

## Context

To list what is due for review, kmctl needs a signal. OKF v0.2 defines
stale_after (a date), verified (who confirmed a concept and when) and
sources (what it was written from). A covers field mapping a concept to the
code it describes would give a sharper signal; the spec allows extension
fields.

## Decision

Use only the spec's fields for now: due when stale_after has passed, when a
concept has no verified entry, or when a file in its sources changed in git
after its last verified date.

Rejected for now:

- A covers extension field. It needs every concept tagged, and the operator
  wants to keep this simple. Revisit if the spec's fields prove too blunt.
