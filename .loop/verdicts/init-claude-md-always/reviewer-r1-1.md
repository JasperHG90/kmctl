---
type: verdict
title: 'Verdict: init-claude-md-always reviewer round 1'
description: 'reviewer verdict for round 1 of init-claude-md-always: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T17:19:13+00:00'
slug: init-claude-md-always
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. With only AGENTS.md, init adds the block there and writes CLAUDE.md as `@AGENTS.md`, and a second run changes nothing. Dangling links and links outside the repository are left alone with a warning that names the link and its target. Links inside the repository are still written through once. When AGENTS.md is an unsafe link and there is no CLAUDE.md, init writes nothing. The ADR, help, docstrings and reference agree. One edge case does not block: an AGENTS.md that is a directory gets a silent `@AGENTS.md` CLAUDE.md (f1).

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1, r2, r4, r3 all pass; "stamp green: c2cb028f6de178e7916a451c63e1e730c913f93a9de53c789e769f7a8ad006aa". The full suite, tests/test_plugin_install.py included, passed on this run.
- Read the staged diff and all of scaffold.py, the new tests, the ADR 0011 Correction, the log line, commands.md and the init help.
- Ran `kmctl init` in scratch repos. AGENTS.md only, run twice: CLAUDE.md is `@AGENTS.md`, AGENTS.md has one block, `diff -r` against a snapshot shows the second run changed nothing. CLAUDE.md -> AGENTS.md: one block, the link stays. Dangling CLAUDE.md alone: kept, warning, no target and no AGENTS.md created. Dangling CLAUDE.md beside AGENTS.md: AGENTS.md gets the block, the link stays, warning. CLAUDE.md pointing outside (absolute): target unchanged, warning. AGENTS.md pointing outside, and outside but dangling, with no CLAUDE.md: no CLAUDE.md written, target unchanged or not created, warning says "wrote no CLAUDE.md ... fix the link". Root reached through a symlinked folder, with both a relative link and an absolute link that goes through the symlinked folder: written through once, no warning. A self-loop CLAUDE.md: reported as missing, left alone, no crash. AGENTS.md as a directory: see f1. AGENTS.md with broken markers and no CLAUDE.md: writes `@AGENTS.md` and warns about AGENTS.md, which is acceptable because a rerun after the fix adds the block.
- Eval rows. r1: the agents_only tests check that AGENTS.md keeps its text and has exactly one block (`_block` asserts one start and one end), that CLAUDE.md is exactly `@AGENTS.md\n`, that the empty repo gets the block, and that a second run leaves bytes and mtimes unchanged (`_snapshot`). An importing CLAUDE.md is checked to stay byte-identical. r2: the unsafe_link tests cover a dangling CLAUDE.md alone and beside AGENTS.md, outside links for both files, a dangling or outside AGENTS.md with no CLAUDE.md (no CLAUDE.md, warning names AGENTS.md and says to fix the link), and an in-repo chain reached through a symlinked root, written through with one block over two runs. r4: the test asserts that the dated Correction names `@AGENTS.md` and symlinks, and that help, both public docstrings, the reference and the log mention `@AGENTS.md`. r3: the whole file passes.

## Findings

- f1 (bug, not blocking): `has_agents = os.path.lexists(agents)` counts a directory or other non-file AGENTS.md as present. The loop then skips it (`not path.is_file()`), and init writes CLAUDE.md as `@AGENTS.md` with no warning, so no file holds the block. I reproduced this in scratch case j. The plan's lexists rule is about not replacing a dangling CLAUDE.md. It does not need the import file to point at something that is not a file. The fix is small: write the import only when AGENTS.md resolves to a file, and fall back to the block otherwise, or add a warning.

## Notes

The earlier flaky run of tests/test_plugin_install.py (6 failures that passed on rerun) does not come from this change: those tests run the real claude CLI and add a marketplace from GitHub over the network, and this diff touches no plugin code. The suite passed in my stamp run. The flakiness is still a real pre-existing problem in the gate, because network failures can turn the stamp red at random. It deserves its own ticket, for example a retry, or a marker that keeps network tests out of the default gate.
