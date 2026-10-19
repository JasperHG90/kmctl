---
type: decision
title: "ADR 0030: Projects commit what APM deploys"
description: "A project commits the files apm install and kmctl plugin patch deploy for its harnesses and gitignores only apm_modules/, as APM's guide says."
tags: [adr, decision, apm]
generated:
  by: process:kmctl/0.10.0
  at: 2026-10-19T08:04:36Z
status: stable
---

# ADR 0030: Projects commit what APM deploys

## Context

`just bootstrap` in a starter project runs `apm install` for the targets in
`apm.yml`, then `kmctl plugin patch`. Together they write the skills, rules
and agents into `.claude/`, `.agents/` and `.opencode/`, and hook and MCP
entries into `.claude/settings.json`, `.mcp.json`, `opencode.json`,
`.agents/hooks.json` and `.agents/mcp_config.json`. APM keeps its download
cache in `apm_modules/`.

PR #16 (issue #15) proposed gitignoring every installed path, so that a
second machine's install or an upgrade would not show up as a diff. The
operator closed it on 2026-10-19 ("Ok close it. Ensure that apm_modules is
gitignored").

## Decision

A project commits what APM and `kmctl plugin patch` deploy, and gitignores
only `apm_modules/`. That is APM's own guidance: its "What to commit" table
marks `.github/`, `.claude/` and `.agents/` "Yes, deployed agent files" and
`apm_modules/` "No", restored by `apm install`
([workflow.md](https://github.com/microsoft/apm/blob/main/packages/apm-guide/.apm/skills/apm-usage/workflow.md)).
`starter/.gitignore` ignores `apm_modules/`, and `tests/test_starter.py`
checks it.

Rejected, PR #16: ignoring the deployed paths. It would hide shared project
config the team edits too (`.claude/settings.json` is Claude Code's
checked-in settings; the per-user file is `settings.local.json`), and leave
a fresh clone, or a cloud agent that only clones, without skills, rules or
the briefing hook until someone runs `just bootstrap`. The harnesses are the
`targets` in the committed `apm.yml`, so they do not differ per user.

## Consequences

- A clone works for an agent before anyone installs anything.
- An upgrade shows up as a diff to the deployed files as well as to
  `apm.yml` and `apm.lock.yaml`; review reads the lock and skims the rest.
- If an install on a second machine changes files nobody edited, that is a
  bug in the install output to fix, not a reason to ignore the files.
