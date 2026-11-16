---
type: verdict
title: 'Verdict: decision-gaps-skill plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of decision-gaps-skill: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T16:18:16+00:00'
slug: decision-gaps-skill
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved. The plan now judges one change at a time
in batches of about ten, with a subagent per batch where the harness has
them, asks to narrow past about forty changes, reports record-only changes
apart, and adds a known-answer eval scored against the prototype's labels.
Both install pages are in touches, and r1 checks that they count eight
skills. Nothing else I found could break the plan, and Problems, Goals and
Outcomes match the prose.

## Checked

- p1: the Intent now describes per-change judging in batches, subagents
  where the harness has them, a narrowing prompt past about forty changes,
  record-only changes listed apart (the prototype's last advice), and a
  known-answer eval. r1 checks the body's batching, narrowing and
  record-only instructions; r2 requires the known-answer prompt and its
  counts against labels.json in results.md.
- Known-answer range is feasible: I ran the dependency's
  `kmctl decision candidates` (worktree loop/decision-candidates) against
  this repo. `--since 14799749` gives 163 changes. `--since 2cf55821c`
  (the parent of prototype unit 105) gives 57 changes holding four labelled
  gaps (ce8b712c, 09af291c, da6a34c5, c92c6e0d), a labelled false alarm
  (642d7236), and several recorded-in-unit changes. The labels key on the
  same merge shas the verb lists (ce8b712c shows up in its output).
- p2: both install pages are in touches. The "seven skills" text is at
  install-kmctl-with-apm.md:141 and install-the-plugin-and-the-ci-action.md:95
  and :137. r1's behaviour names the eight-skill count.
- The `__init__.py` touch is gone. The dependency's `candidates` epilog and
  `--json` help already name the decision-gaps skill (worktree
  `__init__.py` ~938-985), so dropping it is correct.
- Facts: there is one behaviour outcome, which fixes P1 and serves G1, has
  no needs, and touches the skill, its evals, the three test files, the new
  how-to page, the generated how-to index and both install pages. That is
  everything the prose says changes. P1 is one cause and the outcome can
  ship alone, since depends_on covers decision-candidates.
- Round 1's checks of harness reach, wheel inclusion, the briefing token
  budget and the eval-row commands still hold. Nothing in those areas
  changed.

## Findings

- p1: resolved. Judging is now per change in batches, long lists get a
  narrowing prompt, and r2 requires a known-answer range scored against the
  labels.
- p2: resolved. Both install pages are in touches and r1 checks the count.

## Notes

- `kmctl decision candidates` has `--since` but no end point, so every
  known-answer range runs to HEAD. Any range holding more than one or two
  labelled gaps has more than forty changes (57 for the four late gaps), so
  the eval run will hit the skill's narrowing prompt. Its prompt should
  tell the skill to go ahead, or say the run answers "go ahead". This is a
  builder detail, not a risk to the plan.
- In a live run, the prototype's hidden positives (ADR-adding units) count
  as covered, and claims on changes the prototype never labelled can't be
  scored from labels.json. So results.md's precision needs those claims
  labelled by hand, and its recall is over labelled gaps in range, not the
  prototype's hidden-decision recall. The builder should state that
  difference when comparing numbers.
