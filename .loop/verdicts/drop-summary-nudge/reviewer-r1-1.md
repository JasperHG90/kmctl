---
type: verdict
title: 'Verdict: drop-summary-nudge reviewer round 1'
description: 'reviewer verdict for round 1 of drop-summary-nudge: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T05:37:07+00:00'
slug: drop-summary-nudge
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The code reversal is clean. For src/, apm/ and tests/, the tree differs from ac764a8f (before both nudge tickets) only by later, unrelated changes: the version bumps, the briefing hook's new description, the release-workflow tests, the ADR 0014 corrections test, and the four new tests. So nothing unrelated to the nudge was undone. `_flat_commands` matches what `hook_present` needs: APM writes the SessionStart and Stop handlers flat, and only the PostToolUse handlers needed the nested form. All gates and rows are green. One stale sentence about the after-tool hook is left in .okf/summary.md (f1), and there are three small doc and test fixes. None needs a second review.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and integration pass; eval rows r1 to r4 pass; `stamp green: bc39f53c...`.
- `git diff ac764a8f -- src apm tests` shows only post-nudge commits (3063014d, the 0.9.1 release, the workflow tests) plus the new tests. `git diff ac764a8f -- .claude README.md docs .okf/manifesto.md .okf/summary.md .okf/architecture` shows ADR 0004 changed to 0029 and edits from later commits that are kept, plus f1.
- Read the staged diff in full for __init__.py, antigravity.py, doctor.py, opencode.py, plugin.py and summary.py. There are no orphaned imports (ruff passes). The OpenCode plugin's `cwd` refactor went back to its pre-nudge inline form. The doctor epilog and the run_doctor docstring no longer list nudge-hook checks.
- Rows: r1 is test_package_ships_no_post_tool_use_hook (both hooks.json files, no PostToolUse key) plus test_plugin_has_no_after_tool_hook (no execute.after in PLUGIN_SOURCE). r2 is test_summary_has_no_nudge_verb (help has no nudge, `summary nudge` exits non-zero) plus test_doctor_has_no_nudge_check (see f4). r3's shell grep covers its paths but not .okf/summary.md, which is how f1 got through. r4 is the full suite.
- ADR 0029 is accurate on the reasons: the briefing line `summary behind: N ... changed` is in briefing.py:268, the AGENTS.md duty is in scaffold.py:52, and `review due` reads the summary. It is also accurate on what was removed and on the 0.25 s cost. ADR 0028 is `status: deprecated` with a dated Correction pointing to 0029, and the index marks it superseded.
- Grepped docs/, README.md, .claude/rules/, the manifesto, the architecture overview and the summary for nudge, PostToolUse, execute.after, "two hooks", ADR 0028 and ADR 0004.

## Findings

- f1: summary.md lines 42-43 describe the dropped hook as live. Delete the sentence and run `kmctl summary ack`, or re-check the summary, as needed.
- f2: The superseding line is duplicated at the end of ADR 0029.
- f3: The manifesto (line 133) and docs/explanation/why-one-hook-and-report-only-audits.md (line 70) cite the deprecated ADR 0004 as the current rule. This is the pre-nudge wording put back unchanged; ADR 0029 is now the current record.
- f4: The r2 doctor test does not cover OpenCode's former check.

## Notes

The .claude/skills/rule-creator hits for "nudge" use the ordinary English word and have nothing to do with this ticket.
