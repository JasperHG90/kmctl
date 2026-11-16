---
type: verdict
title: 'Verdict: decision-candidates reviewer round 2'
description: 'reviewer verdict for round 2 of decision-candidates: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T16:34:45+00:00'
slug: decision-candidates
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both findings sent back are fixed. `candidates()` now finds the top level with `git rev-parse --show-toplevel` and reads the newest record from HEAD's tree. Run from a subdirectory or with a staged record, the verb gives the same list as from the root of main. The words signal folds whitespace before it matches. One small docs gap came with the fix: the reference page does not list the new no-commits refusal (f3, not blocking).

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2 and r3 all pass, `stamp green: 8d14eb4b95a85f6d0fef4b4eb676455dd447ef50779f6430609c7322aae86f3e`.
- I ran pytest on `tests` (495 passed) and `packages/kmctl/tests` (947 passed) separately, and each eval row's command alone (7, 5 and 66 passed).
- Read `candidates.py` in full. `default_since` runs `git ls-tree --name-only HEAD .okf/decisions/` at the top level, so the paths are full and match `DECISION`. Four-digit numbers sort correctly as strings. The CLI passes `path.resolve()` and `candidates()` replaces it with the top level before `_plan` and `_intent` read `.loop/`.
- Live check in this worktree, where 0047 is staged but not committed: `kmctl decision candidates` from `packages/kmctl`, from the worktree root, and with `--path` set to the primary checkout each list 2 changes. In round 1 the first two listed 165.
- `--since bc6f0ebe^ --json`: bc6f0ebe now has `words: true`, which matches the prototype.
- New tests: `test_split_default_ignores_a_decision_not_yet_committed` stages 0002 and expects EXPECTED, which the old working-tree glob would fail because it lists Start. `test_split_from_a_subdirectory_reads_the_whole_repository` runs with `--path repo/src/app`, checks the full set and the plan path, and would fail under the old code. `test_fields_words_signal_reads_across_line_breaks` uses "instead\nof". `test_refuses_a_repository_with_no_commits` checks exit 1 and the fix line. The tests fall under the r1, r2 and r3 `-k` filters.

## Findings

- f1: resolved at `candidates.py` `default_since` and the top-level lookup in `candidates()`. Tests and the live run above confirm it.
- f2: resolved at `_signals` (`" ".join(text.split())`). A test was added and bc6f0ebe now matches.
- f3: `docs/reference/commands.md` says "Exit code: 1 when kmctl refuses (not a git repository, or a `--since` that names no commit)". The fix added a third refusal, for a repository with no commits, which the docstring names and the page does not. Add it to that list.

## Notes

- The default text in the help and the reference ("after the commit that added the newest decision record") could say "newest committed decision record", now that uncommitted records are ignored on purpose. That is optional.
