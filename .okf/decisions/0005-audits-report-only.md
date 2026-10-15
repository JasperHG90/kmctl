---
type: decision
title: "ADR 0005: Audits report only, and CI runs them in two tiers"
description: "The audit agent and its review skills report findings and never write knowledge or verified stamps; the reusable GitHub Action runs free deterministic checks on every PR and an opt-in LLM audit."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
decision_status: Accepted
decided_on: 2026-10-15
---

# ADR 0005: Audits report only, and CI runs them in two tiers

- Status: Accepted
- Date: 2026-10-15

## Context

Knowledge drifts and no deterministic check catches all of it, so an agent
has to judge. An agent that both judges and edits the knowledge can quietly
make it agree with itself.

## Decision

- One audit agent uses three skills: architecture review (does the design
  match the code), decision-log review (does each decision still hold, or has
  a later one or the code overtaken it) and practices review (does each
  practice still have the evidence it cites).
- It reports findings. It never edits .okf/ or docs/ and never writes a
  verified stamp. A person, or an agent the person asks, acts on them.
- The reusable GitHub Action has two tiers: the deterministic checks on every
  pull request, at no model cost, and the LLM audit only when a repository
  opts in. Both report as a job summary or comment.

Rejected:

- The audit writes verified stamps when a concept passes. The operator chose
  report only.
