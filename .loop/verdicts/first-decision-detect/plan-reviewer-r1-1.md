---
type: verdict
title: 'Verdict: first-decision-detect plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of first-decision-detect: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T14:30:56+00:00'
slug: first-decision-detect
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan holds. Changing the guard in `_write_first_decision` from a title match to "no `*.md` other than `index.md` in `.okf/decisions/`" is a small, local change with nothing that could stop it. Its list of risks says none, and I found none that would break it.

## Checked

- `src/kmctl/scaffold.py`: `_has_first_decision` (line 317) and the guard at line 411 are where the plan says, and are the only callers. `scaffold()` calls `_write_first_decision` last, after `_files` and `fix_folder_indexes`, so a fresh run reaches it with no records and the new rule still writes `0001`.
- `src/kmctl/concepts.py` `_next_number` numbers from the `*.md` files in the section, so emptying the records in the copied-bundle tests gives `0001`, as the plan expects.
- `tests/test_init.py`: `test_init_first_decision_not_written_twice`, `test_init_reports_kept_files_it_changed_as_updated` and `test_init_human_output_names_why_each_file_was_updated` copy this repo's `.okf/` and expect a write. Under the new rule they would write nothing, which the plan already names and handles. `test_init_first_decision_kept_when_title_exists` keeps passing because records are present.
- The text that states the title rule appears only where the plan lists it: the `scaffold()` docstring, the `kmctl init` epilog (`src/kmctl/__init__.py:81`), `docs/reference/commands.md:88` and ADR 0011 line 54.
- `.okf/decisions/` holds 30 records and none has the first decision's title, which matches the measured case.

## Findings

None.

## Notes

`kmctl check` counts a section's pages with `rglob` (`src/kmctl/checks.py:225`). The plan's rule uses a flat `*.md` glob, so a decision log moved into a subfolder of `.okf/decisions/` would still get a duplicate. That is an edge case for the build to settle (glob or rglob), not a reason to rethink the plan.
