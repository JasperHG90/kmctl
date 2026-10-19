---
type: decision
title: "ADR 0031: A decision record may be draft until it is accepted"
description: "A decision record may carry status draft while its choice awaits acceptance; once accepted its status becomes stable and a log.md line records it."
tags: [adr, decision, okf]
generated:
  by: process:kmctl/0.10.0
  at: 2026-10-19T14:34:35Z
status: stable
---

# ADR 0031: A decision record may be draft until it is accepted

## Context

The okf-bundle rule said a decision's `status` is `stable` or `deprecated`,
in all three copies (`apm/claude/.apm/instructions/okf-bundle.instructions.md`,
the Antigravity copy generated from it, and `.claude/rules/okf-bundle.md`).
The schema accepts `draft` too (`STATUS_VALUES` in `src/kmctl/kinds.py`, as
OKF v0.2 section 5.4 does), and `kmctl check` passes a decision marked
`draft`. Issue #27 asked which one is meant: a team that writes down a
choice before it is accepted could not tell. The operator chose to allow
`draft`.

## Decision

A decision record may carry `status: draft` while its choice waits to be
accepted. Once it is accepted, its `status` becomes `stable` and a line in
`log.md` says so. That edit is the one change a record takes besides an
appended `## Correction, YYYY-MM-DD` section and what
`kmctl decision supersede` writes. A draft differs from a proposal in
`proposals/`: a draft holds one choice, a proposal weighs options before
there is one. The okf-bundle rule says this in all three copies.

Rejected, the other route in issue #27: refuse `draft` for decisions in the
schema and send choices not yet accepted to `proposals/`. kmctl would then
reject a value OKF v0.2 allows, and a team that writes the record first and
accepts it later would have to move the file between sections.

## Consequences

- A record can exist before its choice is accepted; readers check `status`
  before they act on it.
- The rule's body changed, so the okf-bundle hash in `OLD_RULES` in
  `tests/test_apm_package.py` moved, with its comment naming this record.
- None of this repository's 30 earlier decisions is `draft`, so no record
  changes.
