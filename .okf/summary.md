---
type: summary
title: "Summary: kmctl"
description: "The whole of kmctl in at most 500 words: what it is for, how its parts fit, what its records settle and where it stands, citing the concepts; start here."
generated:
  by: claude-opus/5.5
  at: 2026-10-18
tags: [summary]
checked:
  at: 2026-10-19T01:08:38Z
  against:
    - decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script
---

# Summary: kmctl

## The project

kmctl keeps a repository's knowledge current: `docs/` for people who use a
project, an `.okf/` bundle for people and agents working on it. Since
nothing can force knowledge to stay true, kmctl puts it in front of the
agent at every session start and audits it; a person decides
([manifesto](manifesto.md)). It serves maintainers and their agents in
Claude Code, Antigravity and OpenCode.

## How it works

Four parts ([overview](architecture/overview.md)). The CLI in `src/kmctl/`
alone writes knowledge. An APM package in `apm/` carries skills, an audit
agent, four knowledge rules and two hooks; APM installs it and
`kmctl plugin patch` fills APM's gaps. A GitHub Action runs free checks on
each pull request and an opt-in LLM audit. A copier template starts new
projects pinned to a release.

An agent reads in layers: the SessionStart hook injects `kmctl briefing`,
the block in `CLAUDE.md` and `AGENTS.md` points to this summary, the summary
to the indexes, and the indexes to the concepts. When a concept changes
after this page, an after-tool hook asks the agent to update it. Each
project pins kmctl in `apm.lock.yaml`, and the `kmctl` on PATH hands every
command to that release
([ADR 0026](decisions/0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins.md)).
Handoffs in `.okf/handoffs/` carry unfinished work into the next session
(`/handoff`, `/continue`;
[ADR 0008](decisions/0008-handoffs-are-okf-concepts.md)).

## What it has settled

- **Prompts may, code must.** Verbs write the numbering, front matter,
  index entries, log lines and `docs/` folder indexes; the agent writes the
  prose, and skills only route to verbs
  ([ADR 0001](decisions/0001-standalone-cli-installs-its-plugin.md),
  [ADR 0008](decisions/0008-handoffs-are-okf-concepts.md),
  [ADR 0022](decisions/0022-docs-pages-carry-optional-okf-front-matter-and-generated-folder-indexes.md)).
- **Inject, don't link.** An agent reads a page only if it
  knows to look, so knowledge arrives through two hooks that never block,
  plus rules where the briefing alone left too few records written
  ([ADR 0002](decisions/0002-briefing-and-rules-injected-by-the-cli.md),
  [ADR 0028](decisions/0028-two-hooks-the-session-briefing-and-the-summary-nudge.md),
  [ADR 0011](decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md)).
  Antigravity also relays okf's Stop check
  ([ADR 0018](decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity.md)).
- **OKF as it is.** kmctl uses the spec's fields plus two named extensions,
  `handoff_key` and `checked`, so any bundle works; staleness comes from
  `stale_after`, `verified`, `sources` and commit order, with no `covers`
  field
  ([ADR 0006](decisions/0006-staleness-from-okf-fields.md),
  [ADR 0009](decisions/0009-handoff-key-extension-field.md),
  [ADR 0027](decisions/0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md)).
- **Judging is not trusting.** Audits report and never write; only a person
  verifies, and an agent's `kmctl summary ack` is no review. The CI
  audit takes any provider and never runs beside a GitHub token
  ([ADR 0005](decisions/0005-audits-report-only.md),
  [ADR 0017](decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md),
  [ADR 0023](decisions/0023-kmctl-verify-records-a-person-s-check.md)).
- **One version, one owner per file.** The package matches the CLI's
  version. APM owns what it installs; kmctl patches only its gaps, each
  until APM closes it
  ([ADR 0014](decisions/0014-apm-is-the-only-install-route.md),
  [ADR 0020](decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md),
  [ADR 0021](decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md)).
  CI makes releases, and each tag releases the template too
  ([ADR 0012](decisions/0012-releases-come-from-ci.md),
  [ADR 0025](decisions/0025-the-starter-template-lives-in-kmctl-and-shares-its-release-tags.md)).

The [decision index](decisions/index.md) lists every record.

## Where it stands

All four parts work, for the three harnesses. Invariants I1, I3 and I4 are
enforced by tests; I2, that audits never write knowledge, is still
`planned`. No practices, proposals or prototypes are recorded, and many
concepts have no `verified` entry, so `kmctl review due` lists them. Work in
flight lives in `.loop/` tickets, outside the bundle.
