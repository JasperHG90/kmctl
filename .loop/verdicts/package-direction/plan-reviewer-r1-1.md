---
type: verdict
title: 'Verdict: package-direction plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of package-direction: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T11:36:51+00:00'
slug: package-direction
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan holds. A new decision is the right place for the rule, since a stable record such as ADR 0043 or 0044 may only take an appended correction and the rule is a new choice rather than a correction. 0046 is the next free number. No test, rule or check pins the root README or CLAUDE.md in a way the plan breaks.

## Checked

- `.okf/decisions/` ends at 0045. No remote branch adds a file numbered 0046 to 0049, and the untracked decision-gaps-measure plan claims no decision number.
- `.claude/rules/okf-bundle.md` says a record is never rewritten and a correction is an appended section. So amending 0043 or 0044 would be the wrong move, and linking 0043 from a new record fits. The manifesto links to decisions and never repeats them (`docs-layout.md`), so leaving it alone is consistent.
- `tests/test_readmes.py`: the root README must stay under 80 lines (it is about 50 now), must link both package READMEs and docs/, and every relative link must resolve. A link to the new decision resolves once the file exists. `_root_entry` splits each entry on `**[pkg](` and on the next `- `, so a direction clause and a link inside the entry leave the badge and beta tests working.
- CLAUDE.md is a symlink to AGENTS.md, which has no managed kmctl block. No test in tests/ or packages/*/tests reads this repository's CLAUDE.md (the test_init hits are for tmp repos), and `checks.py` does not mention it.
- `kmctl new decision TITLE --description ...` exists and writes the front matter, skeleton, index entry and log line. The planned filename is about 86 characters, shorter than the existing 100-character names.
- Problems, Goals and Outcomes: there is one problem, one goal and one behaviour outcome that can ship alone, and `needs: none` is right. Its touches cover what the prose says changes, plus log.md and summary.md, which the bundle rules require. The eval rows match the checked-by line.
- The plan lists no risks under "Could invalidate this plan", and I found none that would break it.

## Findings

None.

## Notes

Things for the build, not the plan: `kmctl new decision` may write `status: draft`, and the operator has already settled this rule, so set `stable` and add the log line the rule asks for. Also update `.okf/summary.md` in the same change.
