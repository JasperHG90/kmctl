---
type: decision
title: "ADR 0003: The Claude Code plugin comes first and depends on the okf plugin"
description: "kmctl ships a Claude Code plugin first, declaring okf@scaccogatto as a dependency; other harnesses follow and use the okf author's skills or MCP server."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: deprecated
---

# ADR 0003: The Claude Code plugin comes first and depends on the okf plugin

- Status: Accepted
- Date: 2026-10-15

## Context

OKF authoring and validation already exist in the okf plugin by Marco Boffo
(github.com/scaccogatto/okf-skills, marketplace scaccogatto). Claude Code
supports plugin dependencies
(https://code.claude.com/docs/en/plugin-dependencies).

## Decision

- Build the Claude Code plugin first; other harnesses after it works.
- Declare okf as a dependency. It lives in another marketplace, so kmctl's
  marketplace.json lists scaccogatto in allowCrossMarketplaceDependenciesOn,
  and the dependency is declared in the marketplace entry, so a missing
  allowlist refuses the install instead of installing a plugin that then
  fails to load.
- No version range for now: a range resolves against okf--vX.Y.Z git tags
  in the okf repository, and it is not yet checked that those exist.
- For other harnesses, kmctl uses the okf author's skills or MCP server
  instead of a plugin dependency.

Rejected:

- Copy the okf skills into kmctl. Two copies drift.
- All harnesses at once. Each has its own hook and plugin format; one that
  works first shows what the others need.

## Correction, 2026-10-15

The record had no Consequences section; this adds it.

### Consequences

- `kmctl plugin install` adds the scaccogatto marketplace before
  installing, because `claude plugin install` does not add a dependency's
  marketplace by itself.
- With no version range, any okf release installs; a breaking okf change
  reaches kmctl users without warning.
- Only Claude Code is supported so far; other harnesses get the briefing
  only if they run `kmctl briefing` themselves.

## Correction, 2026-10-16

Superseded by [ADR 0014](0014-apm-is-the-only-install-route.md).

The other harnesses follow through APM: Antigravity in
[ADR 0015](0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder.md).
