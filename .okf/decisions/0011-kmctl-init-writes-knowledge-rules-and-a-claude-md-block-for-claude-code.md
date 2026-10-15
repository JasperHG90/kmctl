---
type: decision
title: "ADR 0011: kmctl init writes knowledge rules and a CLAUDE.md block for Claude Code"
description: "kmctl init writes four knowledge rules to .claude/rules/, a kmctl block into CLAUDE.md and AGENTS.md, and a first decision; the briefing stays the cross-harness path."
tags: [adr, decision, init, rules]
generated:
  by: claude-opus/5.5
  at: 2026-10-15T16:13:16Z
status: stable
---

# ADR 0011: kmctl init writes knowledge rules and a CLAUDE.md block for Claude Code

- Status: Accepted
- Date: 2026-10-15

## Context

An agent in a repository set up with `kmctl init` wrote code and left the
bundle nearly empty: it made 6 design choices and recorded 1, wrote no
architecture page, and left the manifesto's values empty. A fresh
`kmctl init` wrote four files and nothing else, so the agent got a briefing
and empty templates. In this repository knowledge stays current because of
things kmctl did not ship: rule files loaded by path, a `CLAUDE.md` that
routes to `.okf/`, and a seeded bundle.

[ADR 0002](0002-briefing-and-rules-injected-by-the-cli.md) rejected native
rule files per harness, because only some harnesses have them. The briefing
it chose is at 526 of its 600 words (I3), so the two rules it lacks
(`diagrams-stay-current`, `manifesto-invariants`) do not fit in it.

A spike (loop spike `init-seeds-the-habit/1`, one FastAPI task, three runs
per arm) compared init plus the briefing with the same plus the seeding
below: architecture pages went from 0 of 3 runs to 3 of 3, and decisions
recorded from a mean of 3.0 to 4.3.

## Decision

`kmctl init` also seeds the habit, for Claude Code first
([ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md)):

- It writes the knowledge rules `okf-bundle`, `docs-layout`,
  `diagrams-stay-current` and `manifesto-invariants` to `.claude/rules/`, in
  full with their WHY paragraphs and `paths:` front matter, from package data
  in `src/kmctl/repo_rules/`. These copies are written for any repository. An
  existing file of the same name is kept.
- It adds a block between `<!-- kmctl:start -->` and `<!-- kmctl:end -->` to
  each `CLAUDE.md` and `AGENTS.md` that exists, once per real file, so a
  `CLAUDE.md` symlinked to `AGENTS.md` gets one block; with neither, it
  writes `CLAUDE.md`. The block holds the routing table and three duties:
  record each choice as a decision, keep `.okf/architecture/` matching the
  code, run `kmctl check` before finishing. A re-run replaces only the block.
- It records the decision "Keep project knowledge in an OKF bundle" through
  `kmctl new decision`'s writer when no record has that title.
- Its last line names the next steps: the manifesto's purpose and
  invariants, an architecture page once there is code, and a decision for
  each choice.

This reverses, for Claude Code only, the alternative ADR 0002 rejected
(native rule files per harness). The briefing stays the cross-harness path
and keeps its two one-line rules from `src/kmctl/rules/`, unchanged. The
CLAUDE.md block carries the gist of the other two rules for any harness that
reads `CLAUDE.md` or `AGENTS.md`.

Rejected:

- Add the two rules to the briefing. They take it past its 600-word budget
  (I3).
- Leave init as it was and rely on the briefing. The spike's unseeded arm
  wrote no architecture page in any run.
- Write rule files for every harness. Each has its own format, which is
  ADR 0002's reason, and the plugin is Claude Code first.

## Consequences

- `kmctl init` no longer leaves every kept file alone. The exceptions are the
  kmctl block in `CLAUDE.md` and `AGENTS.md` and the first decision's index
  entry and log line; `ScaffoldResult` and `kmctl init --help` name them.
- Two copies of the knowledge rules ship in the package: the briefing's
  one-line forms in `src/kmctl/rules/` and the full files in
  `src/kmctl/repo_rules/`. A change to a rule changes both.
- A repository that edits a seeded rule keeps its edit; init never
  overwrites it, so an upgrade does not reach it.
- Every new bundle starts with decision 0001, so a user's first
  `kmctl new decision` is numbered 0002.
