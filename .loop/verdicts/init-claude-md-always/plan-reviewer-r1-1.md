---
type: verdict
title: 'Verdict: init-claude-md-always plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of init-claude-md-always: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T16:33:45+00:00'
slug: init-claude-md-always
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works and the operator's direction is clear, but three gaps need fixing before the build. p1: the contract contradicts itself on a dangling CLAUDE.md link, because "missing" is undefined. p2: the plan rests on an unchecked premise about whether Claude Code reads AGENTS.md, and it does not say what the new CLAUDE.md holds; a spike answers the first part. p3: the scope leaves out ADR 0011, the docs, the help, and an existing test that asserts the old behavior. Nothing here forces a rethink, and the ticket does not need splitting.

## Checked

- The plan's risk list is "none", and no spike folder exists for this slug.
- Read `_write_block`, `_with_block` and `AGENT_FILES` in the init-seeds-the-habit worktree's src/kmctl/scaffold.py. The loop skips any entry where `is_file()` is false, which includes dangling links. The final `(root / "CLAUDE.md").write_text(BLOCK)` runs only when no real file was seen, and it follows a dangling link to create the link's target. That confirms the round 1 note and shows where the new write must check `lexists`.
- Read the round 1 review notes, ADR 0011's Decision and Consequences, docs/reference/commands.md, and tests/test_init.py, including the symlink test (CLAUDE.md -> AGENTS.md gets one block) and the AGENTS.md-only replace test that asserts no CLAUDE.md.
- Read the eval rows r1-r3 against the Intent.

## Findings

- p1: "missing" is undefined for a dangling CLAUDE.md link, so r1 and r2 can disagree. Define missing as no directory entry, and test the dangling-CLAUDE.md-plus-AGENTS.md case.
- p2: if Claude Code falls back to AGENTS.md, a new CLAUDE.md that holds only the block hides AGENTS.md from it. A harness that reads both files also gets the block twice. Spike the fallback, then choose what the new CLAUDE.md holds.
- p3: ADR 0011, the docs, the help and test_init.py:249 all encode the old rule. The plan should name each change.

## Notes

- "Outside the repository" needs to mean `link.resolve()` is not under `root.resolve()`. Compare against the resolved root, not the path as given: a root reached through a symlink (macOS /tmp -> /private/tmp, some tmp_path setups) would otherwise flag every in-repo link as outside. Chained links resolve fully under `resolve()`. A link to an existing file inside the repo (CLAUDE.md -> AGENTS.md, or CLAUDE.md -> docs/agents.md) must still be written through once, and the existing symlink test keeps that in r3.
- A dangling link whose target is inside the repo (CLAUDE.md -> AGENTS.md with no AGENTS.md) is left alone under the plan as written. That is safe and consistent. Leaving a dangling CLAUDE.md link alone also means no CLAUDE.md gets written in that repo, which is the right call, and p1 asks only that the contract say so.
- The two parts of the ticket (always write CLAUDE.md, and link safety) touch the same function. Splitting them is not needed.
