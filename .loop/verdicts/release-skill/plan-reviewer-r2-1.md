---
type: verdict
title: 'Verdict: release-skill plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of release-skill: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:51:44+00:00'
slug: release-skill
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The revisions close both round 1 findings. The gap step no longer regenerates
reviewed notes (p1), and the after-merge step reads release-tag's late-commit
warning (p2). The eval rows test what they claim, and I found no new risk that
could break the plan.

## Checked

- Re-read the revised plan and the re-signed rows r1 to r4.
- release-per-package's plan (line 70) has release-tag publish the reviewed file unchanged and write a `::warning::` plus a step-summary section naming late commits, "so someone adds them with `gh release edit`". Step 4 reads exactly those, and step 5 adds them by hand. That closes p2 and fits D3.
- release-per-package commits the notes as `.github/release-notes/TAG.md`, the path step 5 edits. release-tag's push paths are `apm/apm.yml` and `packages/kmaudit/VERSION` only, so a follow-up commit to the notes file does not set off a second tag or publish.
- release-notes-hermes keeps the draft when Hermes fails. Either way the committed file is the reviewed text, so "never regenerate, edit both by hand" holds in both cases. That closes p1.
- Problems, Goals and Outcomes still match the prose. P1 now names the missing late-commit read, and P2 names the regenerate fix that would overwrite reviewed notes. O1 is the one behaviour, O2 and O3 are support and need O1, and touches cover the skill, the rule and the new test.
- r2 now has a matching test named so `-k explains` selects it, and the placeholder-as-glob rule is in the plan and in r1.

## Findings

- p1: resolved. The gap step is now hand edits to the Release and the committed file, never regenerated.
- p2: resolved. Step 4 watches the release-tag run and reads its late-commit warning and step summary.

## Notes

- r4 runs `-k "release_tag or gap"`, but the plan never says the tests carry those names. Neither the module name nor the plan's wording guarantees a match, so the builder must name the after-merge and gap tests with `release_tag` and `gap`, or r4 collects nothing. This is the same kind of build detail as round 1's `explains` note.
- The follow-up commit to `.github/release-notes/TAG.md` lands on a protected main, so it probably goes through a small pull request. The skill should say that rather than tell someone to push to main. Build detail.
