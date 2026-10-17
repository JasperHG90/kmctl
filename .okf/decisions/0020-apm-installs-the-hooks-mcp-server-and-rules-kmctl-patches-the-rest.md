---
type: decision
title: "ADR 0020: APM installs the hooks, MCP server and rules; kmctl patches the rest"
description: "kmctl's APM package ships its SessionStart hooks, okf's MCP server and per-harness rules in sub-packages; kmctl writes only what APM cannot install yet: Antigravity agents and the fix for okf's Antigravity Stop hook."
tags: [adr, decision, install, apm, antigravity]
generated:
  by: process:kmctl/0.3.0
  at: 2026-10-17T14:20:56Z
status: stable
sources:
  - resource: "apm/apm.yml"
  - resource: "apm/claude/apm.yml"
  - resource: "apm/antigravity/apm.yml"
  - resource: "src/kmctl/plugin.py"
  - resource: "src/kmctl/antigravity.py"
  - resource: "scripts/sync_antigravity_rules.py"
---

# ADR 0020: APM installs the hooks, MCP server and rules; kmctl patches the rest

## Context

Since [ADR 0014](0014-apm-is-the-only-install-route.md) kmctl wrote some of
its install itself: the Claude Code SessionStart hook and okf's MCP server,
and for Antigravity a plugin folder holding the agents, the rules
([ADR 0016](0016-antigravity-rules-come-from-the-kmctl-plugin-folder.md)),
the hooks and the MCP server
([ADR 0015](0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder.md),
[ADR 0018](0018-kmctl-runs-okf-s-stop-check-for-antigravity.md)). Each came
from a narrow spike that APM did not do it, not from APM's documentation as
a whole. The operator asked (2026-10-17) to hand back to APM everything APM
can do and to document what it cannot.

A review of apm-cli 0.33.0's source (the newest release) and the ticket's
spikes found:

- A package can ship hooks (`.apm/hooks/hooks.json`); APM merges them into
  `.claude/settings.json` and `.agents/hooks.json`, records what it wrote in
  `apm-hooks.json`, and keeps every command byte for byte
  (spike:apm-hands-back/3).
- A package can declare an MCP server under `dependencies.mcp`. APM trusts a
  direct dependency's server and writes it to `.mcp.json`,
  `.agents/mcp_config.json` and, with `-g`, the user `.claude.json`; it skips
  a transitive one, which is why kmctl's package declares okf's server
  itself (spike:apm-hands-back/1, /5).
- A package can depend on sub-packages by relative path, each with its own
  `targets:`, so each harness gets only its own rules and hooks
  (spike:apm-hands-back/1). APM resolves every sub-package whatever the
  target, so each needs an `.apm/` folder (spike:apm-hands-back/4).
- agy loads a SessionStart hook from the workspace `.agents/hooks.json` under
  APM's hook name `apm`, and okf's server from `.agents/mcp_config.json`
  (spike:apm-hands-back/2).
- APM writes an Antigravity rule's several globs as a YAML list, which agy
  refuses; written in `applyTo` as `**/` globs joined by escaped commas
  (`\,`), they come out as the one string agy reads
  (spike:apm-hands-back/1). The `\,` escape is meant for a comma inside one
  glob, so this leans on APM's parser.

## Decision

kmctl's package is three APM packages in `apm/`:

- `apm/` (shared): the skills, kmctl-auditor, the okf-skills dependency,
  okf's MCP server `okf-bundle` under `dependencies.mcp` (kmctl's `sh`
  launcher at the pinned okf commit), and `./claude` and `./antigravity`.
- `apm/claude/` (`targets: [claude]`): the four rules, and the SessionStart
  hook running `kmctl briefing`.
- `apm/antigravity/` (`targets: [antigravity]`): the four rules, generated
  from the Claude copies by `scripts/sync_antigravity_rules.py` (a test fails
  when a copy is stale); the SessionStart hook running
  `kmctl briefing --format antigravity`; and ADR 0018's okf Stop wrapper,
  now running from `.agents/`.

`kmctl plugin install` writes none of these. It removes, before running APM,
what an older kmctl wrote that APM now writes, at project and user scope: a
kmctl SessionStart group APM's `apm-hooks.json` does not record, and an
`okf-bundle` entry that differs from the package's. `kmctl doctor` checks the
files APM writes.

What APM cannot do yet, and what kmctl does meanwhile:

| Gap | Stopgap | Drop it when |
|---|---|---|
| APM writes no agents for Antigravity (APM issue #2990, accepted, unreleased; it will not translate tool names either). | kmctl writes `.agents/plugins/kmctl/` with `plugin.json` and the agents translated from Claude Code's format. | APM ships agents for Antigravity and kmctl's package can ship an Antigravity-format agent file in `apm/antigravity/`. |
| APM writes okf's Antigravity Stop hook as `bash ".agents/hooks/okf-skills/hooks/okf-stop-check.sh"`, a path from the repository root, but agy runs hooks in `.agents/`; okf also prints Claude Code's `"block"`. No APM issue is filed. | kmctl takes that handler out of `.agents/hooks.json`; the package's wrapper runs okf's check instead (ADR 0018). | APM writes Antigravity hook paths relative to `.agents/`, or okf ships target-specific hook files with agy's output. |
| `apm uninstall -g` leaves `okf-bundle` in the user `.claude.json` (spike:apm-hands-back/5); at project scope uninstall removes it. | None; the install how-to gives `claude mcp remove okf-bundle --scope user`. | APM removes a user-scope MCP server on uninstall. |
| A consumer whose `apm.yml` has an `allowExecutables` block gets no hook or MCP server from a package it does not allow. | None; the how-to says to allow kmctl's package. | Not an APM bug: the consumer's choice. |
| A user with their own okf server under another name now gets `okf-bundle` as well; kmctl used to add none then. | None; doctor passes either way. | APM can skip a server another entry already provides. |

Rejected:

- Keeping kmctl's own writers. Two owners of the same hook and server meant
  two copies of each after an `apm install`, and state APM did not record.
- One Antigravity rule file per glob, which works without the escape. It
  turns four rules into a dozen files and splits each rule's guidance.

## Consequences

- `apm install` (or `apm update`) alone keeps the hook, rules and MCP
  server current; `apm uninstall` removes them.
- kmctl's remaining install-time work is the two stopgaps above; the next
  ticket moves it to `kmctl plugin patch`.
- ADR 0016 is superseded: the rules come from APM again, in the form agy
  reads. ADRs 0014, 0015 and 0018 point here for what changed.

Supersedes [ADR 0016](0016-antigravity-rules-come-from-the-kmctl-plugin-folder.md).
