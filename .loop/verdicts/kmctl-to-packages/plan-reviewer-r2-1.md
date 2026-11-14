---
type: verdict
title: 'Verdict: kmctl-to-packages plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmctl-to-packages: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T19:53:19+00:00'
slug: kmctl-to-packages
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Fail. Round 1's findings are resolved: spike 5 settles the hook risk with evidence from both tools, and the outcome facts now match the prose. Two new findings remain, both fixable by revision. p5: O1 still leaves CI red without action.yml and the starter's kmctl_src, which sit in O3. p6: the v0.12.1 cutoff meets test fixtures that tag the moved tree as v0.12.1, so the starter and pin integration tests would install from the root and fail.

## Checked

- Risk 1: spikes 1 and 3. Risk 2: operator acceptance. Risk 3: spikes 2 and 4 (1407 selected; 876/276/255 matches the plan's counts).
- Risk 4: spike 5. The README outcome matches stdout's summary: (a) fails in both tools, (b) works in both, `uv sync --locked` passes with no root package. Limit noted by the spike: the hook repo was a local path, not a GitHub URL. That is not a plan risk.
- Outcomes: every non-O1 outcome needs O1 and nothing else. O2 and O3 are separate behaviours, and each can follow O1 once p5 moves action.yml and the starter into O1.
- Eval r5 now searches packages/kmctl/tests.

## Findings

- p1: resolved by spike 5.
- p2: resolved. O1 holds the move. The leftover gap is p5.
- p3: resolved. Every other outcome needs O1.
- p4: resolved. release.py now sits in P2.
- p5: action.yml (the knowledge job every CI job needs) and the starter's kmctl_src belong in O1.
- p6: tree_repo tags the moved tree v0.12.1, so the cutoff gives no fragment and the starter and pin integration tests install from the root.

## Notes

- With p5 fixed, the starter's kmctl_src change lands in O1, and O3 keeps the fixed install lines, hints and release.py.
- One ticket is still right. The risks are settled or fixable, and none of them calls for a split.
