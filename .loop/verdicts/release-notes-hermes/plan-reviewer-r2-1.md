---
type: verdict
title: 'Verdict: release-notes-hermes plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of release-notes-hermes: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T20:01:18+00:00'
slug: release-notes-hermes
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved. Spike 3 tested the real action runner at the pinned SHA, in the tools-off setup the plan now uses, and every rewrite passed the checks. The plan now handles changes in meaning with a stricter prompt and puts the draft beside the rewrite for the person who merges. No open risk could break the plan.

## Checked

- Read the revised plan, eval rows r1 and r2, and the round 1 verdict.
- Read spike 3's README, run.json (exit 0, not truncated) and the stdout summary. Config B is the plan's exact disabled_toolsets list with max_iterations 3, and it shows kept 15/15, 0 runs using tools, 0 flagged reversals. Config A shows 10 runs calling tools and adding detail the draft lacks, which is why tools off is the better choice.
- Read release-per-package's plan: the draft step runs in its own notes job (in dry runs too), and the Hermes step goes into the same job. Bump downloads the notes artifact and builds the PR body. To fill the "Draft before Hermes" block, bump also needs the draft's What changed section, so the notes job has to hand it over (for example in the same artifact). That is a build detail inside `release.yml`, which O2 already touches and r2 checks. It is not a plan risk.
- Problems, Goals and Outcomes match the prose. O1 (support, fixes P2, seen by nobody) cannot ship alone. O2 (behaviour, needs O1, fixes P1) now lists the toolsets, max_iterations and the draft block in its check, and its touches cover the workflow, prompt, workflow test and ADR 0035, as the prose says.

## Findings

- p1: resolved; spike 3 ran the action's runner at the pinned SHA, and the plan pins tools off.
- p2: resolved; the stricter prompt plus the draft shown beside the rewrite in the PR body puts the meaning check with the merger, which risk 2 states.

## Notes

The ticket is still small enough to stay in one piece.
