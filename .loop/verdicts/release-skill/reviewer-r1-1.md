---
type: verdict
title: 'Verdict: release-skill reviewer round 1'
description: 'reviewer verdict for round 1 of release-skill: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T22:34:36+00:00'
slug: release-skill
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The skill is accurate and plain. It answers both of the operator's questions. release.yml opens the version pull request, and release-tag.yml tags the merge commit on the later push to main. release-tag is not an APM workflow, but it watches apm/apm.yml because users pin the APM package to the CLI tag. Notes are guaranteed because release-tag refuses a missing or blank notes file. The rule shrank to the two constraints and points at the skill. Two small non-blocking fixes remain: the version input's format in the skill, and a loose check in the test that looks for advice to regenerate notes.

## Checked

- Ran `loopctl gate stamp` from the worktree. It passed lint, format, tests, integration and eval rows r1 to r4: "stamp green: c19b70de402217c7a0a829101a3074e42dd3e73fab82bb70ad62d937a430d32a".
- Checked every claim in SKILL.md against release.yml and release-tag.yml. That covered the inputs and their options, the dry-run step summary (it names the notes source), the off-main refusal, the `release/<tag>` branch, the notes committed as `.github/release-notes/<tag>.md` via `mkdir -p`, the PR body holding the notes plus the before-hermes section, the push-path trigger, one matrix job per package with "nothing to release" for the other, the missing-or-blank refusal, the late-commit `::warning::` and the "Commits missing from the <tag> notes" summary heading, and "only kmctl is Latest". I also checked the cited scripts (release_notes.py, hermes_release_notes.py --before, next_release_version.py, where --version is required with no tag yet). `gh run list --commit` exists in the installed gh.
- Eval rows. r1's tests check the name, the inputs against the parsed release.yml, the packages against the input's options and the paths, and they include negative tests for a made-up input and a missing path. r2's two `-k explains` tests check the needed phrases inside the "Why two workflows" section. r3: `-k rule` selects all of test_rules.py plus the three rule tests, which check both constraints, gh release edit, the committed file, release_notes.py and "never regenerated". r4: the step 4 and step 5 section tests check the run commands, the warning, both edit targets and the ban on regenerating. f2 is the only weakness I found.
- The builder's open decision on `.github/release-notes/`: the path rule accepts a placeholder folder only when release.yml has `mkdir -p <folder>`, so it is tied to the real workflow and fails if that line goes. Adding the folder to test_rules' PLANNED is consistent with how `packages/` and `docs/` are handled. A placeholder file would be worse: it would sit in the folder release-tag reads notes from. I accept the deviation from the plan's wording.
- releases.md: the cited paths exist, and the reworded every-release-has-notes matches the plan's D3 wording.

## Findings

- f1: the skill's `version` bullet leaves out the pre-release form that release.yml's input description allows. Fix the docs only.
- f2: the regenerate check in the test exempts any sentence containing "not". Tighten it so a ban only counts when it comes before the verb.
