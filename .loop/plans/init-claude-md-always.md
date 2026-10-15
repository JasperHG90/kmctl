---
type: plan
title: 'Plan: init-claude-md-always'
description: "kmctl init writes CLAUDE.md with the kmctl block whenever it is missing, even when AGENTS.md exists, as the operator asked, and never writes through a CLAUDE.md or AGENTS.md symlink that is dangling or points outside the repository."
slug: init-claude-md-always
epic: knowledge
depends_on: [init-seeds-the-habit]
priority: 3
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:32:01+00:00'
---

# init-claude-md-always

Relayed from: operator, 2026-10-15: "CLAUDE.md --> either append when doing init or write if it doesn't exist." init-seeds-the-habit's review (round 1 notes) found two gaps against that.

## Intent

After init-seeds-the-habit, `kmctl init` adds its block to each existing `CLAUDE.md` and `AGENTS.md`, and writes `CLAUDE.md` only when neither exists. Two gaps:

- A repository with only `AGENTS.md` gets the block there and no `CLAUDE.md`. Claude Code 2.1.300 loads `AGENTS.md` only while there is no `CLAUDE.md`, and any `CLAUDE.md` hides it unless it imports it with `@AGENTS.md`, which loads it exactly once (spike:init-claude-md-always/1). So with `AGENTS.md` and no `CLAUDE.md`, init adds the block to `AGENTS.md` and writes a `CLAUDE.md` whose only content is `@AGENTS.md`: Claude Code then reads the operator's instructions and the block once each, and a tool that reads both files gets the block once. With neither file, init writes `CLAUDE.md` with the block, as now. The operator's direction, "write if it doesn't exist", holds in both cases.
- A `CLAUDE.md` or `AGENTS.md` that is a symlink to a missing file, or to a file outside the repository (its resolved path not under the resolved repository root), makes init create or edit that target. Init leaves such a link alone with a warning naming it and where it points. A file counts as missing only when no directory entry exists (`os.path.lexists` is false), so a dangling `CLAUDE.md` link is never replaced and no new `CLAUDE.md` is written beside it. A link inside the repository, such as `CLAUDE.md` to `AGENTS.md`, is written through once as now.

What changes with it: ADR 0011's Decision says "with neither, it writes CLAUDE.md", so it gets an appended dated Correction naming the `@AGENTS.md` case and the link rule; `docs/reference/commands.md`, init's help and the scaffold docstrings say the same; and `test_init_claude_md_replaces_only_the_block`, which asserts no `CLAUDE.md` is written beside an `AGENTS.md`, changes to expect the import file.

Measured with init-seeds-the-habit's build: in a repository with only `AGENTS.md`, 0 of 1 runs leave a `CLAUDE.md`; a dangling `CLAUDE.md` link makes init create its target, outside the repository when the link points there (round 1 review note). Spike 1 shows the fix: case 4 (`AGENTS.md` plus a `CLAUDE.md` of `@AGENTS.md`) loads `AGENTS.md` once in 2 of 2 runs.

Done when a test shows init in a repository with only `AGENTS.md` adds the block to `AGENTS.md` and writes `CLAUDE.md` holding only `@AGENTS.md`; a test shows a dangling link and a link outside the repository are left alone, their targets not created or changed and no new `CLAUDE.md` written, with a warning naming each; a link inside the repository is still written through once; ADR 0011 has the Correction and the help, docstrings and reference say the same; and the other init tests pass.

## Could invalidate this plan

- Settled by spike:init-claude-md-always/1 for Claude Code 2.1.300: a `CLAUDE.md` hides `AGENTS.md` unless it imports it, and `@AGENTS.md` loads it exactly once.
