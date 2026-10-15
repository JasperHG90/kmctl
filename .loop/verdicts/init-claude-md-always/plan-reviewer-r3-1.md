---
type: verdict
title: 'Verdict: init-claude-md-always plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of init-claude-md-always: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T16:39:49+00:00'
slug: init-claude-md-always
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p1 to p5 are resolved. The round 2 revision adds the no-block rule for a CLAUDE.md that imports `@AGENTS.md` (p4) and picks "write nothing, warn" for an unsafe AGENTS.md link with no CLAUDE.md (p5). Each done-when item has a row. No open risk could break the plan, and the ticket does not need splitting.

## Checked

- `_write_block` on main (src/kmctl/scaffold.py:180-211): it skips non-files with `is_file()`, dedups by resolved path and writes CLAUDE.md when nothing was seen. That is where both gaps live: `is_file()` is false for a dangling link, so `seen` stays empty and the fallback writes through it; and a real CLAUDE.md holding `@AGENTS.md` would get the block on rerun. The plan's rules (lexists for "missing", resolved-root check, import-line skip) each change one of these branches, so the approach fits the code.
- Rows against done-when: AGENTS.md-only block plus import file, and the second-run no-op, map to r1; dangling and outside links left alone with warnings, no CLAUDE.md beside a dangling one, the in-repo link written through once, and the unsafe AGENTS.md link with no CLAUDE.md map to r2; ADR Correction, help, docstrings and reference map to r4; "other init tests pass" maps to r3.
- tests/test_init.py: `test_init_claude_md_replaces_only_the_block` (line 238) is the test the plan says changes; `test_init_claude_md_symlink_gets_one_block` (252) and `test_init_twice_with_existing_agent_files_changes_nothing` (374) cover the in-repo link case and should keep passing.

## Findings

- p1 resolved: the lexists rule is in Intent and r2.
- p2 resolved: spike:init-claude-md-always/1 settles the premise.
- p3 resolved: every change is named and r4 checks the text.
- p4 resolved: the import-line rule is in Intent and r1 runs init twice.
- p5 resolved: write nothing and warn, tested in r2.

## Notes

- Left to the build: a real CLAUDE.md with `@AGENTS.md` while AGENTS.md is a dangling link. Under the plan neither file gets the block and AGENTS.md gets a warning, which tells the operator what to fix. That is fine.
- "Nothing is written" in the unsafe AGENTS.md case means no agent file is written; the rest of init (docs, bundle, rules) still runs. r2's fails_when reads it that way.
