---
type: summary
title: "Summary: kmctl"
description: "What kmctl's bundle knows, theme by theme, in at most 500 words; start here."
generated:
  by: claude-opus/5.5
  at: 2026-10-18
tags: [summary]
---

# Summary: kmctl

kmctl keeps a repository's knowledge current: `docs/` for people who use a
project, this `.okf/` bundle for people and agents working on it. It puts
the right knowledge in front of the agent at every session start and audits
the rest, because nothing can force knowledge to stay true. The
[manifesto](manifesto.md) holds the purpose, the parts and the invariants.

## Decisions

- **A CLI that does the bookkeeping.** kmctl is a standalone Typer CLI
  ([ADR 0001](decisions/0001-standalone-cli-installs-its-plugin.md)) whose
  briefing a SessionStart hook injects
  ([ADR 0002](decisions/0002-briefing-and-rules-injected-by-the-cli.md),
  [ADR 0004](decisions/0004-sessionstart-is-the-only-hook.md)). The kmctl on
  PATH runs the release a project's lock pins
  ([ADR 0026](decisions/0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins.md)).
- **APM installs the package.** Skills, the audit agent, rules, hooks and
  okf's MCP server come from APM; `kmctl plugin patch` adds only what APM
  cannot install yet, for Antigravity and OpenCode
  ([ADR 0021](decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md),
  [ADR 0024](decisions/0024-opencode-gets-the-package-from-apm-and-its-agents-rules-and-briefing-from-kmctl-plugin-patch.md)).
- **Staleness from OKF's own fields.** `kmctl review due` reads
  `stale_after`, `verified` and `sources`
  ([ADR 0006](decisions/0006-staleness-from-okf-fields.md)); only a person
  verifies ([ADR 0023](decisions/0023-kmctl-verify-records-a-person-s-check.md)).
  The only extension fields are `handoff_key` and `checked`
  ([ADR 0009](decisions/0009-handoff-key-extension-field.md),
  [ADR 0027](decisions/0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md)).
- **Audits report only.** CI runs the free checks on every pull request and
  an opt-in LLM audit, a standalone PydanticAI script for any provider
  ([ADR 0005](decisions/0005-audits-report-only.md),
  [ADR 0017](decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)).
- **Setting a repository up.** `kmctl init` writes the bundle, a block in
  `CLAUDE.md` and `AGENTS.md` and a first decision
  ([ADR 0011](decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md));
  `docs/` pages carry optional OKF front matter and generated folder indexes
  ([ADR 0022](decisions/0022-docs-pages-carry-optional-okf-front-matter-and-generated-folder-indexes.md));
  a copier template starts new projects
  ([ADR 0025](decisions/0025-the-starter-template-lives-in-kmctl-and-shares-its-release-tags.md)).
- Releases come from CI ([ADR 0012](decisions/0012-releases-come-from-ci.md)).
  The full list, with what each replaced, is the
  [decision index](decisions/index.md).

## Architecture

The [overview](architecture/overview.md) shows the four parts: the CLI in
`src/kmctl/`, one module per verb and the only part that writes knowledge;
the APM package in `apm/`; the GitHub Action in `action.yml` and `action/`;
and the starter template. `okf.py` is the one reader of front matter, and
`kinds.py` the one table of document kinds.

## Open work

No proposals or prototypes are recorded in the bundle. Work in flight lives
as loop tickets in `.loop/`, outside it.

## Practices

No practices are recorded yet.

## Known gaps

- Invariant I2, that audits never write knowledge, is still `planned`: no
  test enforces it ([manifesto](manifesto.md)).
- Many concepts have no `verified` entry, so `kmctl review due` lists them.
- Out of scope for now: a `covers` field, hooks beyond SessionStart, and
  harnesses beyond Claude Code, Antigravity and OpenCode.
