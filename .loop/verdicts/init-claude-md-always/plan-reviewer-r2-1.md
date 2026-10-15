---
type: verdict
title: 'Verdict: init-claude-md-always plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of init-claude-md-always: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T16:37:53+00:00'
slug: init-claude-md-always
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 to p3 are resolved: the plan defines "missing", spike 1 settles the Claude Code premise, and the scope names the ADR, docs, help and test. Two contract gaps remain. p4: on a second run, the current loop appends the block to the new `@AGENTS.md` CLAUDE.md, which loads the block twice and breaks rerun idempotence. p5: the case of an unsafe AGENTS.md link with no CLAUDE.md is not defined. Both are revisions, not a rethink, and the ticket does not need splitting.

## Checked

- Spike 1's README, against p2: the four cases and their counts answer the question for Claude Code 2.1.300. The README states its limits (one version, no other harnesses).
- `_write_block` in the init-seeds-the-habit worktree (src/kmctl/scaffold.py:180-211). It walks CLAUDE.md and AGENTS.md, dedups by resolved path, and appends the block to each real file without one. A CLAUDE.md holding only `@AGENTS.md` is a separate real file, so run 2 appends to it. That is p4.
- tests/test_init.py: `test_init_twice_changes_nothing` (line 48) and `test_init_twice_with_existing_agent_files_changes_nothing` (line 374) use an empty repo and a CLAUDE.md -> AGENTS.md link, so neither catches p4. Line 249 is the assertion the plan says it will change.
- Rows against done-when: r1 matches the AGENTS.md-only and neither cases; r2 matches dangling, outside and in-repo links with warnings; r4 matches the ADR Correction and the help, docstrings and reference; r3 matches "the other init tests pass". Every done-when item has a row.

## Findings

- p1 resolved: the lexists rule is in Intent and r2.
- p2 resolved: spike:init-claude-md-always/1 is cited and the plan follows its outcome.
- p3 resolved: the plan names each change and r4 checks it.
- p4 open: after run 1, a rerun appends the block to the import-only CLAUDE.md. Claude Code then gets the block twice and init changes files on rerun. The plan needs a rule: no block goes into a CLAUDE.md that imports `@AGENTS.md`. r1 should run init twice.
- p5 open: an AGENTS.md that is dangling or points outside the repo, with no CLAUDE.md, has no defined outcome. Each choice has a cost, so the plan should pick one, and r2 should test it.

## Notes

- For p4, checking whether CLAUDE.md contains an `@AGENTS.md` line is enough. Matching the whole file is too strict, because an operator may add lines to it.
- Compare outside-ness against `root.resolve()`, as round 1 noted. The plan's "resolved repository root" wording covers this.
