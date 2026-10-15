---
type: verdict
title: 'Verdict: adr-audit-fixes plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of adr-audit-fixes: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:49:00+00:00'
slug: adr-audit-fixes
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan works as an approach, but it rests on one premise that is false on main: the `audit` skill exists. It does not; it arrives with the audit-agent-and-skills ticket, which is still in building and is not a dependency here. That needs fixing before the build, so the verdict is fail. Neither of the two risks the dispatcher asked about breaks the plan.

## Checked

- Removing `decision_status` and `decided_on`: the okf-bundle rule says a record is never rewritten and corrections go in an appended section. The repo already reads this as being about the body. `kmctl decision supersede` (src/kmctl/supersede.py) changes a record's front matter `status` and keeps "its body above that stays as it was". Each of the nine records keeps `- Status: Accepted` and `- Date:` in its body, so dropping the two keys loses nothing. Not a rewrite under the rule as practised, and not a finding.
- I3 budget: `kmctl briefing` prints 432 words on this repo today against WORD_BUDGET = 600 (src/kmctl/briefing.py). One line per skill for four skills is about 40 to 60 words, and even seven would fit. Not a risk.
- Scanned every front matter key in .okf/ against ALLOWED_FIELDS. The only keys not allowed are decision_status (9) and decided_on (9), all in .okf/decisions/. So the planned repo-wide key test passes once those go, and nothing else in the bundle blocks it.
- Consequences: only 0007 and 0009 have a `## Consequences` heading. That matches the plan's 7 of 9.
- Only supersede.py's docstring and tests/test_supersede.py name decision_status in code. The test's fixture adds that key to a tmp bundle on purpose, which this plan does not affect.
- plugin/skills/ on main against the audit-agent-and-skills worktree (/home/vscode/kmctl.worktrees/audit-agent-and-skills, untracked plugin/skills/audit and three review skills). Ticket stage: building.

## Findings

- p1: the `audit` skill the briefing is to name is not on main and comes from an unlisted, unlanded dependency. The meaning of "the kmctl skills" for the new test is not fixed (three today, seven after that ticket lands). Details in the front matter.

## Notes

- The every-touched-concept-is-logged rule covers all nine records, because each loses two front matter keys. 0007 and 0009 count too, even though they get no Correction. The plan mentions a log line only with the Corrections. No gate checks this, so the builder needs to name all nine ids in log.md.
- The eval has no rows yet. The "Done when" sentence lists five checks that each map to a row.
