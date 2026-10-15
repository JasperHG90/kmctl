---
type: verdict
title: 'Verdict: adapt-copied-rules plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of adapt-copied-rules: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T06:05:37+00:00'
slug: adapt-copied-rules
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved. Planned folders may keep their globs, and a kept rule may name loopctl as the tool this repository runs on. The added ADR check is sound: kmctl has ADRs 0001 to 0006, and the copied rules cite 0010 to 0039. One more problem of the p1 kind is left. The path clause would fail references to the .okf/ sections that kmctl's manifesto defines but that are not on disk yet, and several kept rules, including one the briefing ticket builds on, depend on those references. The fix is one sentence, and the scope stays one ticket.

## Checked

- Read the revised plan and my round 1 verdict. The eval has no rows, and there are no spikes. The plan lists no risks.
- Grepped the 12 non-aim rules for backticked paths, ADR numbers, v1/v2, loop-harness/loop_harness and loopctl.
- Listed .okf/: only decisions/ (0001 to 0006), index.md, log.md and manifesto.md. manifesto.md lines 41-42 define the sections decisions/, architecture/, practices/, proposals/, prototypes/ and handoffs/.
- Checked the plans that depend on this one. briefing.md depends on adapt-copied-rules and generalizes its shipped rules from docs-layout.md and okf-bundle.md, which this plan keeps. new-concept-verbs creates the other sections, and audit-agent-and-skills reviews `.okf/architecture/` pages.
- Checked how references between rules hold up after the deletions. okf-bundle cites manifesto-invariants.md, and docs-layout cites okf-bundle.md. The path clause catches links to deleted rules, which is what the plan intends.

## Findings

- p1 (resolved): the four planned folders are now allowed in globs and paths.
- p2 (resolved): loopctl may be named as this repository's ticket tool, and the loop workflow belongs to the plugin.
- p3 (open): the path clause would remove true references to the manifesto's .okf/ sections (architecture/, practices/, proposals/, prototypes/, handoffs/) that do not exist yet. That would gut diagrams-stay-current and the okf-bundle section list the briefing ticket depends on.

## Notes

ci-action adds a root-level `action.yml`, which is outside the four folders. If cli-version-floor should cover it, add it to the allowed list. That is a scoping choice for the builder, not a reason the plan would break.
