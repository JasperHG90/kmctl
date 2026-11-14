---
type: verdict
title: 'Verdict: release-skill plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-skill: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:48:56+00:00'
slug: release-skill
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: a repo-local skill under `.claude/skills/` is tracked and not
apm-managed, `test_rules.py` will resolve `.claude/skills/release/` once O1 lands,
and the outcomes' kinds and needs are right. Two gaps in the after-publish half
must be settled before building. The regenerate-and-edit step conflicts with D3's
reviewed (Hermes) notes (p1). The skill also never reads release-tag's late-commit
warning, which release-per-package counts on someone acting on (p2). Neither needs
a rethink, only a revision.

## Checked

- Read the plan, signed eval rows, the epic brief, and the plans for release-per-package and release-notes-hermes.
- `.claude/skills/` is tracked (frontend-design is committed through apm.lock.yaml) and not gitignored. apm installs only its locked files, so a local `release` skill sits beside them like the local rules do.
- `tests/test_rules.py` `_cited_paths`/`_resolves`: a backticked `.claude/skills/release/` resolves once the folder exists, so O2 needs O1 as stated.
- `.claude/rules/skills-are-thin.md` and `skills-via-skill-creator.md` are scoped by `paths:` to `apm/.apm/skills/**`, so they do not bind this skill. The plan follows skills-are-thin "in spirit", which is fine.
- The prek hooks do not touch `.claude/rules/releases.md` or `.claude/skills/` (Antigravity sync covers only `apm/*/.apm/instructions/`).
- Current `release.yml` inputs are increment, prerelease, version, dry_run. The skill test relies on release-per-package adding `package` (choice kmctl, kmaudit), which its O4 pins.
- Problems/Goals/Outcomes match the prose. O1 is the one behaviour, O2 and O3 are support and cannot ship without O1, fixes and touches line up with the prose.
- "Could invalidate this plan: none". No spike needed. Both findings are contract gaps in the plan text, not questions that running code would answer.

## Findings

- p1: the after-publish regeneration in step 4 and in the reworded `every-release-has-notes` would overwrite the reviewed Hermes/hand-edited notes with the raw draft. It would also make the committed notes file differ from the published Release. The plan must say what a post-publish fix does under D3.
- p2: release-per-package's late-commit warning in the release-tag run is the only signal for commits that ship without a bullet. The skill never reads it, and `gh release view` cannot reveal it.

## Notes

- r2 runs `-k explains`, but the plan's list of what the new test checks (Intent and O1's checked-by) has no explanation test. The builder must add one or r2 collects no tests. The eval is signed, so this is for the builder to notice, not a plan blocker.
- Citing a placeholder path like `.github/release-notes/TAG.md` in the skill will trip the new "every cited path exists" check unless it is written with a `<tag>` placeholder or the test treats placeholders as globs. That is a build detail.
