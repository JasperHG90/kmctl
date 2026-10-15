---
type: verdict
title: 'Verdict: init-seeds-the-habit reviewer round 2'
description: 'reviewer verdict for round 2 of init-seeds-the-habit: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T16:33:52+00:00'
slug: init-seeds-the-habit
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1, f2 and f3 are fixed, and the gates are green on my own stamp. But the f2 fix moved the index and log into `updated`, and the CLI prints every `updated` entry with "(kmctl block)". In a kept bundle the human output now says init put a kmctl block into `.okf/log.md` and `.okf/decisions/index.md`. That is false, and it is the line the fix was meant to make true. The docs and docstrings that define `updated` were not changed to match either. The fix is small, but it needs a test on the human output, so it comes back.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1-r6 and r8 all pass, with "stamp green: 9e8f157e084e4dbcf6885f54f161c61b5544b901c49d3a60a62b7a4dc88d26a3".
- I read `_write_first_decision`, `_marker_problem`, `_with_block`, `_write_block`, the `init` command body and the three new tests.
- In a fresh repo the log reads "- Added `decisions/0001-keep-project-knowledge-in-an-okf-bundle` with `kmctl init`." with no `kmctl new decision` line (f1).
- In a copy of this repo's `.okf`, `--json` lists `.okf/log.md` and `.okf/decisions/index.md` in `updated` and not in `skipped`. `.okf/index.md` and `manifesto.md` stay in `skipped`, which is right because init did not change them (f2). The human output for the same case reads `updated .okf/log.md (kmctl block)` and `updated .okf/decisions/index.md (kmctl block)` (f4).
- Marker cases (f3): an end marker alone gives "has <!-- kmctl:end --> with no <!-- kmctl:start --> before it". A start marker alone gives "has <!-- kmctl:start --> without a <!-- kmctl:end --> after it". Two starts give "has 2 ... and 1 ... markers, not one of each". End before start gives the start-without-end text, which is true for that file. In every case the file is left unchanged.
- The new tests: the log test asserts the `kmctl init` line and the absence of the `kmctl new decision` line. The updated test asserts the JSON lists only, not the human lines. The marker test asserts each message and that the file is unchanged.

## Findings

- f1: resolved. `_write_first_decision` rewrites the log line after `new_concept` (scaffold.py:259-266), and test_init_first_decision_logged_as_init pins it.
- f2: resolved for the result lists. Changed kept shared files move from `skipped` to `updated` (scaffold.py:268-272), and test_init_reports_kept_files_it_changed_as_updated pins the JSON.
- f3: resolved. `_marker_problem` names each broken shape, and test_init_broken_marker_warning_says_what_is_wrong covers three of them.
- f4: new, and caused by the f2 fix. `src/kmctl/__init__.py:100` prints `updated {rel} (kmctl block)` for every entry in `updated`, so the index and log lines claim a kmctl block that was never written. The same assumption still appears in three places. `docs/reference/commands.md:74` says "`updated` (the kmctl block)". The `ScaffoldResult` docstring (scaffold.py:97-101) says only the agent files are "listed in ``updated``". The `scaffold` Returns section says `updated` holds "the agent files whose kmctl block was added or replaced". Fix: give each updated file the right reason, for example "(kmctl block)" for CLAUDE.md and AGENTS.md and "(first decision's entry)" or "(first decision's line)" for the index and log, or keep two lists. Then update the three texts, and add an assertion on the human stdout of the kept-bundle case.

## Notes

- Out of scope as briefed: the AGENTS.md-only case and the dangling CLAUDE.md symlink go to a follow-up ticket.
