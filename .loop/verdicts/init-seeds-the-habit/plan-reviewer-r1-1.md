---
type: verdict
title: 'Verdict: init-seeds-the-habit plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of init-seeds-the-habit: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T16:05:29+00:00'
slug: init-seeds-the-habit
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds and the spike backs it, but three things are left open, and each could break the build or the repo's own rules. The briefing has no room for the two new rules as planned. Writing harness rule files and editing kept files reverses ADR 0002 and init's current contract, and the plan records no decision for that. Decision 0001 is not defined for a repo that already has a bundle, so a second run there would write a duplicate. Each needs a plan revision, not a rethink.

## Checked

- Spike init-seeds-the-habit/1 README, against the plan's one risk. With N=3 per arm, seeding moved architecture pages from 0/3 to 3/3 and decisions from 3.0 to 4.3, and `kmctl check` passed in all six runs. That is enough evidence that seeding helps. r7 reruns it with the built init.
- src/kmctl/scaffold.py: init writes four files and skips any file that exists, and its docstring promises it never edits a kept file.
- src/kmctl/briefing.py: RULE_FILES lists only docs-layout and okf-bundle, and load_rules takes each constraint body minus its WHY. `kmctl briefing` here prints 526 words. The rule lines cost 22 to 41 words each. I counted the four source rules' constraint words without WHY: diagrams 124, manifesto 91, okf-bundle 99, docs-layout 242.
- src/kmctl/concepts.py: the decision skeleton is Context, Decision, Consequences, with no Rejected alternatives section. The okf-bundle rule puts the rejected alternative inside Decision, so the plan's 0001 matches what later decisions get. Not a finding. new_concept takes no body, so init has to fill the sections after the writer runs. That is a build detail.
- ADR 0002 (Rejected, Consequences) and ADR 0003 (Claude Code first). CLAUDE.md here is a symlink to AGENTS.md.
- The source rules in .claude/rules/: okf-bundle names loopctl and .loop/, and docs-layout names .loop/. The plan already requires generic copies, and r1 checks for this.

## Findings

- p1: the briefing budget against the two new rules, and how the full and one-line forms share package data.
- p2: no ADR for reversing ADR 0002's rejected alternative and init's never-edit contract. Includes the AGENTS.md and symlink case.
- p3: decision 0001 and idempotence in a repo that already has decisions.

## Notes

None of these needs a spike. The word counts and the numbering follow from the code. When building the CLAUDE.md write, write through the file in place rather than replacing it, so a CLAUDE.md symlink to AGENTS.md survives.
