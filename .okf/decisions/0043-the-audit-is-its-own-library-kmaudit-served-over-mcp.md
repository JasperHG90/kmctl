---
type: decision
title: "ADR 0043: The audit is its own library, kmaudit, served over MCP"
description: "The audit leaves kmctl for kmaudit, a separate package in packages/kmaudit/ of this repository that runs without kmctl on any folder of markdown docs; kmctl stays at the root, and kmaudit's main interface becomes a stdio MCP server."
tags: [decision]
generated:
  by: claude-opus/5.5
  at: 2026-11-14T11:50:20Z
status: stable
sources:
  - resource: "packages/kmaudit/src/kmaudit/"
---

# ADR 0043: The audit is its own library, kmaudit, served over MCP

## Context

The audit was built inside kmctl as the `kmctl audit` group (ADR 0036 to
ADR 0042): claims, checks, the decision model, the review page and
coverage, with its state in `.kmctl/audit.sqlite`. On 2026-11-14 the
operator decided that kmctl is an optional helper for organising knowledge
with coding agents, and that the audit should not depend on it. Someone who
keeps docs in another layout, or does not use kmctl at all, should still be
able to audit a folder of markdown docs against its repository.

Inside kmctl the audit imported little of it: the front matter reader in
`okf.py` (two modules) and `tracing.py` (one), and nothing in kmctl used
the audit except its CLI group.

## Decision

The audit is its own package, kmaudit, in `packages/kmaudit/` of this
repository, which becomes a monorepo of two packages. kmctl stays at the
root, so its install URLs, the GitHub Action and the release flow do not
move. kmaudit is a uv workspace member: `uv sync` at the root installs it,
and the root gates run its tests beside kmctl's. It imports nothing from
kmctl and carries its own front matter reader; kmctl loses its `audit`
group and its `audit` extra. The shipped agents' guard hook is `kmaudit
guard`.

The direction the operator set, built in the tickets after this one:
kmaudit audits any folder of markdown docs the user points it at (`docs/`,
`.okf/` or another), each folder in its own namespace so two never clash;
its main interface is an MCP server over stdio, so any harness that speaks
MCP (Claude Code, Codex, Antigravity, a LangGraph agent) can drive it; its
CLI only starts the server or the review page, lists namespaces and
database contents, and prints a briefing with summary statistics; and the
`extract-claims` and `write-checks` skills stay, pointing at the MCP tools.

Rejected:

- **Keep the audit in kmctl.** It ties the audit to kmctl's install and
  layout, which the operator no longer wants.
- **Move kmctl into `packages/` too.** Two symmetric packages read more
  tidily, but kmctl's install command, the Action and the release scripts
  all point at the repository root; moving it would break every user's
  install for no gain to the audit.
- **A separate repository for kmaudit.** It would leave the loop, the
  gates and the shared history behind; the two packages still change
  together while the audit settles.

ADR 0036 to ADR 0042 still decide what they decided; read `kmctl audit X`
in them as `kmaudit X`. ADR 0036's correction says where the verbs went.

## Consequences

- The instructions hash that keys each section covers only the extraction
  guidance, not how answers are submitted, so renaming the commands (and
  later moving to MCP tools) keeps every stored answer. A store written
  under the old hash carries its answers over: on this repository's store,
  all 207 sections stayed up to date and its 1,281 claims and 1,137 checks
  stayed.
- Until kmaudit has an install route of its own, the skills and agents in
  kmctl's package call a `kmaudit` command a user cannot install from a
  release. This holds only on the integration branch; the epic adds the
  route before it reaches main.
- The store stays at `.kmctl/audit.sqlite` for now; the namespaces ticket
  moves it.
