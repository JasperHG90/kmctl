---
type: decision
title: "ADR 0013: kmctl installs through APM too"
description: "APM installs kmctl's skills, agent and hook from the apm subfolder package as a second route beside kmctl plugin install; the CLI is still installed with uv tool install."
tags: [adr, decision, install]
generated:
  by: claude-opus/5.5
  at: 2026-10-16T10:50:31Z
status: deprecated
---

# ADR 0013: kmctl installs through APM too

- Status: Accepted
- Date: 2026-10-16

## Context

On 2026-10-16 kmctl's skills and agent reached a repository one way:
`kmctl plugin install`, which stages `plugin/` stamped with the CLI's version
and installs it as the Claude Code plugin `kmctl@kmctl`, after adding the okf
plugin's marketplace
([ADR 0001](0001-standalone-cli-installs-its-plugin.md),
[ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md)). The operator
asked for an install through APM, Microsoft's Agent Package Manager
(`apm-cli` 0.33.0), in release 0.2.0.

APM 0.33.0 reads `plugin/.claude-plugin/plugin.json` as a Claude plugin and
installs `plugin/` as a git subfolder package: the 7 skills and the
`kmctl-auditor` agent byte for byte into `.claude/`, and the SessionStart hook
into `.claude/settings.json`. An apm.yml that declares dependencies inside
`plugin/` makes APM read agents only from `.apm/agents/`, so the agent is
dropped. A consumer of a subfolder package gets none of the root apm.yml's
dependencies, which are this repository's 16 dev rules and skills. APM
requires a `version:` in every apm.yml.

5 of the 7 skills and the agent run a `kmctl` command, so APM can deliver the
files but cannot make them work without the CLI.

## Decision

- `apm/apm.yml`, a folder holding only that file, is kmctl's APM package. It
  depends on `{git: parent, path: plugin}` and on `scaccogatto/okf-skills`
  pinned to a commit. A consumer adds one entry,
  `JasperHG90/Knowledge-management/apm#vX.Y.Z`, and gets kmctl's skills, agent
  and hook plus okf's skills, agents and Stop hook.
- `plugin/` keeps no apm.yml, so the agent is not dropped.
- `plugin/.claude-plugin/plugin.json` stays the one version source
  ([ADR 0012](0012-releases-come-from-ci.md)). The root `apm.yml` and
  `apm/apm.yml` carry copies: `scripts/release.py set` writes them, and
  `scripts/release.py current` refuses when a copy differs.
- APM is a second route beside `kmctl plugin install`, the operator's choice
  on 2026-10-16. `kmctl plugin install` stays the main route.

Rejected:

- Replace `kmctl plugin install` with APM. APM installs the files but not the
  CLI, and it has no counterpart to ADR 0001's version check: the CLI
  installs the plugin of its own release, and `kmctl plugin status` reports
  when the two versions differ. APM cannot see the CLI's version, so it
  would install skills that may not match the `kmctl` on PATH.
- Put an apm.yml in `plugin/`. APM then drops the agent.

## Consequences

- The APM route skips ADR 0001's version check. A user installs the CLI with
  `uv tool install` at the same tag as the APM package, and nothing checks
  that they match.
- The APM route leaves out the kmctl CLI, and okf's MCP server, which APM
  skips as a transitive dependency unless the consumer runs
  `apm install --trust-transitive-mcp` or lists `scaccogatto/okf-skills`
  directly.
- Project scope only: no `apm install -g`. APM refuses `git: parent` at user
  scope.
- While the kmctl repository is private, APM needs GitHub auth with access to
  it.
- `docs/how-to/install-kmctl-with-apm.md` documents the route, and
  `scripts/release.py set` moves its `#vX.Y.Z` pin with each release.
  `tests/test_apm_package.py` checks the package against `plugin/` and
  installs it into a scratch consumer with APM 0.33.0.

## Correction, 2026-10-16

Superseded by [ADR 0014](0014-apm-is-the-only-install-route.md).
