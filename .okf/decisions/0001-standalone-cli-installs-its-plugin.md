---
type: decision
title: "ADR 0001: A standalone kmctl CLI that installs its own plugin"
description: "kmctl is its own tool, not part of loop-harness; it is a Typer CLI that installs its plugin, and the plugin's skills are thin."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
---

# ADR 0001: A standalone kmctl CLI that installs its own plugin

- Status: Accepted
- Date: 2026-10-15

## Context

The knowledge setup in loop-harness v2 (docs/ by Diataxis, an .okf/ bundle,
rules and skills) worked, and the operator wants it in every repository,
including ones that do not run the loop.

## Decision

- kmctl is a standalone package and repository.
- It follows loop-harness ADR 0008: a Typer CLI whose help is written for
  agents, that installs its own plugin from the same release, and whose
  skills route to CLI verbs instead of carrying logic.

Rejected:

- Build it into loopctl. Repositories that do not run the loop could not use it.
- A plugin with no CLI. The briefing, the bookkeeping verbs and the CI checks
  need code that runs the same in every harness and in CI.

## Correction, 2026-10-15

The record had no Consequences section; this adds it.

### Consequences

- One release carries both halves: the plugin is package data, and
  `kmctl plugin install` stages it stamped with the CLI's version, so
  `kmctl plugin status` can report a plugin and CLI that do not match.
- Installing the plugin needs the `claude` CLI on PATH, and the hook needs
  `kmctl` on PATH; without it the hook prints how to install it.
- Skills stay short and call kmctl verbs, so logic lives in tested code.

## Correction, 2026-10-16

The Consequences said the plugin is package data that `kmctl plugin install`
stages stamped with the CLI's version, and that installing it needs the
`claude` CLI. Since [ADR 0014](0014-apm-is-the-only-install-route.md) the
skills, agent and rules ship as the APM package in `apm/`, whose
`apm/apm.yml` carries the release version. `kmctl plugin install --harness
claude` writes that package into the repository's apm.yml at the tag
`v<cli version>` and installs it with APM, so the CLI still installs the
content of its own release, and `kmctl plugin status` compares the ref in
`apm.lock.yaml` with the CLI's version. The wheel carries only the skills,
for `kmctl briefing`; nothing is staged, and the install needs `uv` rather
than `claude` on PATH.
