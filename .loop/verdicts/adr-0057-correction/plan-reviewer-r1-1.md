---
type: verdict
title: 'Verdict: adr-0057-correction plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of adr-0057-correction: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-26T16:47:50+00:00'
slug: adr-0057-correction
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: one appended `## Correction, 2026-11-26` section is how
`.claude/rules/okf-bundle.md` and kmctl's decision kind (a `then` pattern
that allows dated Correction sections after Consequences) say a stable
record changes. Nothing in kmctl check or the summary rules blocks it. One
real risk is unlisted: the Correction could carry over the pre-no-shell text
of 579169c0 and so reverse Roel's rule (p1). Two facts in the 2.0 sections
do not match the prose (p2, p3). Revise; no rethink needed.

## Checked

- Main's ADR 0057 (status stable, with the no-run_shell bullet and the
  matching Consequences) against `git show 579169c0` for the reviewed
  revision. Each of P1 to P4 is a real gap in main's text: there is no 0055
  context, the fork is 'refused', the base checkout is shown as a safeguard,
  'new' and 'fourth' are used without a name, and nothing covers fetch-depth,
  ADR 0046 or publish with no report.
- `action.yml` "Check the event": the refusal is `exit 1`, so P2's premise
  holds. The PR audit is not built yet, so the Correction decides behaviour
  and does not describe code.
- The prototype's ref.txt commit (5ae5e535) is on origin/main, so scope.py
  can be rerun from main. results.txt gives 86 matcher hits, with 0 listed
  for a 'source changed' reason, which matches the plan's figure.
- Stable-decision rules: `kinds.py` lets dated Correction sections follow
  Consequences. `check_summary` reports a behind summary as an error only
  under `--summary-current`, which this repo's CI and pre-commit do not
  pass, and `kmctl check --summary-current` passes on main today. So a summary
  ack is optional here, not a gate.
- The eval rows against the outcomes. None checks that the no-shell rule
  survives (p1).

## Findings

- p1: the Correction may bring back the shell-era key reasoning and the
  missing skill-script constraint from 579169c0, which would overturn Roel's
  accepted no-run_shell rule. The plan and eval need to pin this.
- p2: publish with no report sits in P4 but is delivered by O2, whose fixes
  omit P4. P4 also folds four causes into one problem.
- p3: O1's touches leave out results.txt, ref.txt and the prototype index.

## Notes

All four outcomes edit one section of one file, and O4 being the only
behaviour, waiting on O1 to O3, keeps plan.split from cutting the section
into several tickets. That is the right outcome, so I leave the
behaviour/support labels alone. The operator's choices (fetched --context
folders stay in the working tree; publish with no report exits 0 in every
mode, including issue mode) change accepted behaviour, not just wording. A
person should approve them in the pull request, as they did for the
original acceptance.
