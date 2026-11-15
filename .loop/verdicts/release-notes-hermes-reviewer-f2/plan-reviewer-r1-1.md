---
type: verdict
title: 'Verdict: release-notes-hermes-reviewer-f2 plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-notes-hermes-reviewer-f2: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:03:50+00:00'
slug: release-notes-hermes-reviewer-f2
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. The one listed risk is settled by a
spike, and the repo backs the claims the plan rests on.

## Checked

- Listed risk (the check throws away good rewrites): spike
  release-notes-hermes-reviewer-f2/1. Its script (files/count_stray.py) uses
  the plan's rule (non-blank, not a `- ` bullet, not an indented line after a
  bullet) and found 0 of 16 recorded rewrites would fire. That answers the
  risk for benign drafts.
- Drafts only ever put single-line `- ...` bullets or the literal "None."
  under What changed (scripts/release_notes.py render,
  .github/release-notes*.md templates). So the "same line as the draft"
  exemption only ever covers "None.", and a crafted subject cannot widen it,
  because ticket and PR lines always start with `- `.
- scripts/hermes_release_notes.py `_bullets` (line 70) and `check` behave as
  the plan describes: a lead paragraph is dropped and later lines are joined
  without being checked.
- The 2.0 facts match the prose: one behaviour outcome, fixes P1, touches the
  script and its test file, needs none.

## Findings

None.

## Notes

- `_split` returns the section with its `## What changed` heading line, so the
  new check must skip that line. This is a build detail the tests will catch.
- G1 says "every line Hermes adds carries a reference", but O1 keeps indented
  continuation lines joined onto the bullet above. So an indented,
  unreferenced sentence still passes on its bullet's reference. O1 makes this
  choice openly, and the person merging still sees the "Draft before Hermes"
  block, so the plan holds as written.
