---
type: verdict
title: 'Verdict: okf-summary-holistic plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of okf-summary-holistic: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T21:48:37+00:00'
slug: okf-summary-holistic
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No risk found that could break the plan. The old section names live in one list, `SUMMARY_SECTIONS` in `src/kmctl/kinds.py`, and only tests and the schema read them. No check holds an existing summary to its sections, so v0.8.0 summaries keep working. A Correction on ADR 0027 is the right record under this repo's rules.

## Checked

- Where the section names are used: `SUMMARY_SECTIONS` is read only by `kinds.py` (the summary kind and `kmctl schema summary`), `scaffold.py` (init's skeleton and `SUMMARY_PROMPTS`) and `tests/test_summary.py` (lines 113, 122, 145 and 540, the last one comparing this repository's headings). `checks.py`, `summary.py`, `review_due.py`, `briefing.py` and `action/agent.py` never read sections or `x-kmctl-sections`; `check_summary` counts only words and freshness. So nothing enforces the old names on an existing summary, and `kmctl update` writes a summary only when there is none (`_link_new_pages` adds the index entry only for a page it just created). v0.8.0 summaries do not break; they keep the old shape until someone edits them.
- `SUMMARY_LINE` sets the summary's description and the root index entry for a new bundle only; `_link_new_pages` skips a kept index that already links `summary.md`, so changing the line adds no duplicate entry to an existing bundle.
- The AGENTS.md block: `tests/test_summary.py::test_summary_block_points_to_it_and_gives_the_duty` asserts "add or change a concept" and "update `.okf/summary.md`" in the duty line. Changing the duty's wording has to keep those two phrases or update the test, which the build will show.
- This repository's AGENTS.md and CLAUDE.md hold no kmctl block, so nothing in the repo has to be regenerated from `BLOCK`.
- The record: `.claude/rules/okf-bundle.md` lines 90-92 say a record is never rewritten, a correction is an appended `## Correction, YYYY-MM-DD`, and a reversal is written in both records. ADR 0027 picks the five sections in one bullet with no rejected alternative about them, and its main choice (one summary of at most 500 words, kept fresh by commit order, `summary ack`) stays. Changing the shape is a correction, not a reversal. Ten or more ADRs here already carry Corrections.
- "theme by theme" appears in `scaffold.py`, `.okf/index.md`, `.okf/summary.md`, `.claude/rules/okf-bundle.md` and both `apm/*/okf-bundle.instructions.md` copies. All of these are in the plan's scope, either named or as part of rewriting this repository's summary. `docs/reference/commands.md:65` names the five sections and is in scope.
- No spike was needed: every claim the plan rests on can be checked by reading the code.

## Findings

None.

## Notes

The builder should update the "theme by theme" wording in this repository's `.okf/index.md` summary entry and in the summary's own `description` along with its body, so the root index does not contradict the new shape. That is part of rewriting the summary, not a risk to the plan.
