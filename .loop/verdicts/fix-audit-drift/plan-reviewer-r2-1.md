---
type: verdict
title: 'Verdict: fix-audit-drift plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of fix-audit-drift: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:47:57+00:00'
slug: fix-audit-drift
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

All four round 1 findings are answered, and I found no new risk that could
break the plan. The input is now kept in full, the description and
index-line cases have a fix that matches the bundle rule, the help strings
are in scope, and the rerun has a stopping rule. Verdict: pass.

## Checked

- Spikes 2, 3 and 4: README outcomes, run.json (`exit: 0`, `truncated:
  false` on each), empty stderr. Parsed each stdout.txt as JSON: 7, 21 and 7
  findings, with severities summing to 1 high, 17 medium and 17 low, which
  matches the plan's 35. Each finding has path, claim, contradicted_by and
  fix.
- p2: `.claude/rules/okf-bundle.md` (a record is never rewritten; kmctl
  neither writes nor checks concept counts). `src/kmctl/checks.py`
  `_check_index` checks only that entries link real files and that members
  are listed, not that index text equals the description, so a note after
  the summary will not fail `kmctl check`. `src/kmctl/supersede.py` already
  appends "(superseded by ADR N)" the same way.
- p3: `src/kmctl/__init__.py` docstrings for `review due` (line 300, "List
  concepts in .okf/ due for review") and `briefing` (line 555, "and the
  rules") are the two help strings the okf-vs-docs findings name. The tests
  that read commands.md (test_apm_package, test_antigravity, test_doctor,
  test_new_concept, test_plugin_patch, test_init, test_docs_frontmatter)
  fall under "the tests that pin them".
- p4: Done-when now says one rerun, a returning finding is checked again,
  and a new one goes to a follow-up stub.
- Tutorial: the local kmctl prints `kmctl 0.3.0`, so the rerun of the
  tutorial can be done here.

## Findings

- p1 resolved: spikes 2-4 hold all 35 findings, not cut.
- p2 resolved: descriptions stay, index lines get a note, counts dropped.
- p3 resolved: help strings and their tests are in scope.
- p4 resolved: one rerun, with new findings sent to a follow-up stub.

## Notes

- `kmctl` concept verbs rewrite an index line through
  `concepts._replace_entry`. A later verb that touches one of these
  decisions could drop the hand-added note. That does not affect this
  ticket.
- The rerun needs the same DeepSeek key and model the first audits used.
  They were run from this environment before, so that should be fine.
