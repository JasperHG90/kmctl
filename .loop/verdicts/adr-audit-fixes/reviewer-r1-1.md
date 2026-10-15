---
type: verdict
title: 'Verdict: adr-audit-fixes reviewer round 1'
description: 'reviewer verdict for round 1 of adr-audit-fixes: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:20:36+00:00'
slug: adr-audit-fixes
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. The briefing lists all seven skill folders, read from the plugin payload when it runs. The two fields are gone from all nine records. The seven records gain appended Corrections with Consequences, and nothing above them changed except the front matter the plan removes. The log names all nine records. All gates and rows pass. Three findings remain, none blocking: two Consequences lines overstate the code, the cut-off summaries read poorly, and one format fix is unstaged.

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests and rows r1 to r5 all pass, "stamp green: a035668cbe3399b12cab4f83157116331542c12c411a1193b880764e8c55fdc2".
- Diffed every record against HEAD. The only body changes are the two removed front matter lines and the appended Correction; 0007 and 0009 only lose the two lines.
- Checked each new Consequences line against the code. 0001: plugin.py stage/status/_claude and the hook's install hint. 0002: src/kmctl/rules/ and load_skills. 0003: the scaccogatto marketplace is added first, and marketplace.json has no version range. 0004: hooks.json, plus test_plugin.py tests for a missing and a failing kmctl. 0005: action.yml, knowledge-audit.sh (event guard, the four tools, the one issue) and the auditor's tools list (Read, Grep, Glob). 0006: review_due's shallow-clone and non-git notes. 0008: HANDOFF_DAYS = 14, newest-first sort, expired handoffs in review due. All hold except the two in f1.
- Briefing on this repo: 526 words, against a budget of 600. Each entry is capped at its name plus 12 words, so seven skills add about 100 words.
- Rows: r1 walks nested key paths over all of .okf/ against ALLOWED_FIELDS. r2 accepts a Consequences heading at any level and checks the log for every record. r3 has a real-payload test and a copy with an added skill, monkeypatched through plugin._payload, which skills_dir reads when it runs. r4 is the existing budget test plus the strict validator. r5 is a docstring grep plus test_supersede. None of them is vacuous.
- I4 honesty: _skill_summary's docstring says SKILL.md is Claude Code's format, not an OKF concept. That is accurate, since I4 governs OKF fields, and the okf_fields tests still pass.

## Findings

- f1 (docs, non-blocking): the fixes are plain rewordings. For 0005: "in checks mode it fails when kmctl check fails or review due crashes, never because concepts are due". For 0006: name handoffs as the exception.
- f2 (nit): readability of the cut-off summaries. The fix is cosmetic.
- f3 (nit): stage the formatted briefing.py.

## Notes

action.yml's description has the same "fail only when kmctl check fails" wording as f1. It predates this ticket, but under the pre-existing-issues rule it could be fixed alongside f1.
