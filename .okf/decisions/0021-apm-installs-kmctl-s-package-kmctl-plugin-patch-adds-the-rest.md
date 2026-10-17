---
type: decision
title: "ADR 0021: APM installs kmctl's package; kmctl plugin patch adds the rest"
description: "kmctl plugin install, update and remove give way to apm install, apm uninstall and kmctl plugin patch, which writes only what APM cannot install yet."
tags: [adr, decision, install, apm]
generated:
  by: process:kmctl/0.3.0
  at: 2026-10-17T15:28:49Z
status: stable
sources:
  - resource: "src/kmctl/plugin.py"
  - resource: "src/kmctl/__init__.py"
  - resource: "README.md"
---

# ADR 0021: APM installs kmctl's package; kmctl plugin patch adds the rest

## Context

After [ADR 0020](0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md)
APM installs everything in kmctl's package: the skills, rules, SessionStart
hooks and okf's MCP server. `kmctl plugin install` and `update` still wrote
the `apm.yml` entry and ran APM for the user, and `kmctl plugin remove`
([ADR 0019](0019-kmctl-plugin-remove-uninstalls-the-package-and-reinstalls-the-harnesses-kept.md))
ran `apm uninstall` and installed the kept harnesses again. That wrapper
made kmctl a second front end for APM's own verbs. The operator asked
(2026-10-17) for one command, `kmctl plugin patch`, that replaces install
and update, with installing, upgrading and removing left to APM, and for
the install instructions per harness in the README.

## Decision

APM installs, upgrades and removes kmctl's package: the user adds
`{git: https://github.com/JasperHG90/Knowledge-management.git, path: apm,
ref: vVERSION}` to `apm.yml` (the version of the kmctl CLI they run) and
runs `apm install` (`-g` for Claude Code at user scope), `apm update`, or
`apm uninstall`.

`kmctl plugin patch [--scope project|user] [--json] [--undo]`, run after
`apm install`, adds what APM cannot install yet (ADR 0020's table). It
never runs APM and needs neither uv nor APM on PATH. It reads
`apm.lock.yaml` to see which harnesses APM installed kmctl's package for,
then, for Antigravity, writes `.agents/plugins/kmctl/` (the translated
agents) and takes APM's broken okf Stop handler out of `.agents/hooks.json`;
for Claude Code, it removes what an older kmctl wrote that APM now writes
(saying to run `apm install` again when APM must write it) and the old
claude plugin `kmctl@kmctl`. It refuses, naming the fix, when the lock lists
no kmctl package, and before that when `apm.yml` still names the package as
kmctl v0.3.0 and older did, naming the `apm uninstall` to run first.
`--undo` deletes `.agents/plugins/kmctl/` and nothing else.

`kmctl plugin install`, `update` and `remove`, and the harness question,
leave the CLI. doctor's fixes name `apm install`, the `apm.yml` ref or
`kmctl plugin patch`. The README's install section gives the steps for
Claude Code, Antigravity and both.

Rejected:

- Keeping `install` as a wrapper. It duplicated APM's verbs and kept kmctl
  in the business of writing `apm.yml`.
- Making `patch` run `apm install` itself. The user then needs APM through
  uv for kmctl to work; patch would stop being the small, offline step it is.

## Consequences

- Users need APM (`uvx --from apm-cli==0.33.0 apm` works without installing
  it) and keep the `apm.yml` ref equal to their kmctl version themselves;
  doctor's `claude.lock` and `antigravity.lock` say when they differ.
- `kmctl plugin patch` has to run after every `apm install` or `apm update`
  for Antigravity, since APM rewrites `.agents/hooks.json`.
- ADR 0019 is superseded; ADR 0014 points here for the route.

Supersedes [ADR 0019](0019-kmctl-plugin-remove-uninstalls-the-package-and-reinstalls-the-harnesses-kept.md).
