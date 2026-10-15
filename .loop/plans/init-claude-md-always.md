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

- A repository with only `AGENTS.md` gets the block there and no `CLAUDE.md`, so Claude Code, which reads `CLAUDE.md`, never sees it. The operator asked for `CLAUDE.md` to be written when it does not exist. Init writes `CLAUDE.md` with the block whenever it is missing, and still adds the block to `AGENTS.md` when that exists.
- A `CLAUDE.md` or `AGENTS.md` that is a symlink to a missing file, or to a file outside the repository, makes init create or edit that target. Init leaves such a link alone with a warning naming it and where it points.

Measured with init-seeds-the-habit's build: in a repository with only `AGENTS.md`, 0 of 1 runs leave a `CLAUDE.md`; a dangling `CLAUDE.md` link makes init create its target, outside the repository when the link points there (round 1 review note).

Done when a test shows init in a repository with only `AGENTS.md` writes `CLAUDE.md` with the block and adds the block to `AGENTS.md`; a test shows a dangling link and a link outside the repository are left alone, their targets not created or changed, with a warning naming each; and the other init tests pass.

## Could invalidate this plan

- none
