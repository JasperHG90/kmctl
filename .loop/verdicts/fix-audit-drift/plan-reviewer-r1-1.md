---
type: verdict
title: 'Verdict: fix-audit-drift plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of fix-audit-drift: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:45:41+00:00'
slug: fix-audit-drift
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: check each finding against the code, add Correction
sections to decisions, edit the manifesto, architecture page and docs with
log lines, and rerun the tutorial. Four gaps should be fixed before the build
starts. The spike that is meant to hold the input has only 11 of the 35
findings (p1). The plan does not say how to fix the findings that sit in a
decision's description or index line (p2). Some of the wrong text comes from
CLI help strings, which are outside the plan's scope (p3). The fresh-audit
Done-when has no stopping rule (p4). None of these means the plan must be
rethought, so the verdict is fail, not reject. One ticket is still the right
size.

## Checked

- Read the plan and the eval (0 rows). Read the spike README, run.json
  (`truncated: true`) and stdout.txt: 11 finding titles, starting partway
  through okf-vs-code. Listed all 35 from the scratchpad report.json files
  and read each audit's summary.
- Decisions: okf-bundle.md (a record is never rewritten; a correction is an
  appended section). Checked git history for any edited `description:` in a
  decision and found none. Read ADR 0012's front matter and its corrections,
  ADR 0001's corrections, and decisions/index.md lines 20-32, which copy each
  description.
- Tutorial rerun: the local `.venv` kmctl prints `kmctl 0.3.0`. The v0.3.0
  tag's version source (plugin.json) is also 0.3.0, so the high finding is
  real, and a rerun with the current kmctl can be done here. Read through the
  tutorial's commands: none needs the network or Claude.
- commands.md compared with the docstrings in src/kmctl/__init__.py, and the
  tests that read commands.md.
- The 'one hook' explanation page compared with ADR 0004's 2026-10-17
  amendment and the manifesto's Parts section.

## Findings

- p1 (premise): the spike's stdout is cut off and holds 11 of the 35
  findings, so the ticket's input is not kept anywhere the build can rely on.
- p2 (missing): the plan does not say how to fix findings in a decision's
  description or index line, which a Correction section cannot reach.
- p3 (missing): the scope leaves out the CLI help strings that commands.md
  rows copy, so fixing only the docs leaves `--help` wrong.
- p4 (design): the fresh-audit Done-when has no stopping rule for a model
  whose output varies between runs.

## Notes

- The 'one hook' finding (docs-vs-code #2 and okf-vs-docs #0): ADR 0004's
  amendment says kmctl's own hook is still SessionStart only and that the
  operator chose this. The fix should probably be wording such as "kmctl's
  own hook" plus a mention of okf's opt-in Stop check, not a change to the
  claim. Changing the claim would mean changing ADR 0004 and I1, which the
  operator decided. Checking the finding against the code, as the plan says,
  should catch this, but watch for it.
- `.okf/index.md` concept counts: okf-bundle.md says kmctl neither writes
  nor checks counts, so removing the counts may be a better fix than
  updating them.
- Line numbers from the audits are stale for overview.md, ADR 0017 and the
  CI how-to since langfuse-traces landed. Building will sort that out; it
  does not affect the plan.
