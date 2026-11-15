---
type: verdict
title: 'Verdict: release-per-package reviewer round 1'
description: 'reviewer verdict for round 1 of release-per-package: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T21:29:23+00:00'
slug: release-per-package
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. Both workflows take or loop over the package. The tag families stay apart in every script that reads tags. The notes are drafted in a job that also runs in dry runs, committed on the drafted commit with a Drafted-From trailer, refused before tagging when missing or blank, and published unchanged. Only a kmctl release that is not a pre-release is marked Latest. There are two findings, neither blocking: a gap in finding the drafted commit (f1) and two stale docstrings (f2).

## Checked

- Gates: `loopctl gate stamp` was refused by this session's permission classifier, so I could not re-stamp. Instead I ran `uv run pytest tests/scripts` (200 passed) and `uv lock --check` (clean). I also ran each eval row's command: r1 4 passed, r2 21 passed, r3 8 passed, r4 7 passed, r5 22 passed.
- r1: the tests read pyproject's dynamic regex source, check that VERSION holds 0.1.0.dev0 and that compare prints skip, check that uv.lock has no kmaudit version line, and build the file's version.
- r2: newest_tag and increment tests mix v* and kmaudit-v* tags. `set --package kmaudit` is checked to write only its two files. kmctl's set is checked to be unchanged, and the tag verb is covered.
- r3: the scratch repo has both tag families. The kmaudit draft starts at kmaudit-v0.1.0 and the kmctl draft at v0.2.0, each with an exact bullet list. The first-draft walk is covered, and so is refusing the other family's tag.
- r4: bump's script runs in bash against a bare origin. The tests check the branch parent equals DRAFTED, the trailer, the exact set of changed files, the committed notes, and that the PR body holds the notes and the trailer. Structure tests cover the notes job having no `if`, the artifact handoff and the checkout ref.
- r5: the refusal step runs before build and tag and has the same `if` as publish. The bash tests cover missing, empty and blank notes. The publish step passes the file byte for byte, with the right Latest flags for kmctl, kmaudit and a pre-release. The late-commit step runs in bash for merge and squash, for both packages, naming only that package's commits, leaving out loop commits, and leaving the notes file unchanged. With no trailer it warns and does not fail.
- Workflow shell: every input and output reaches the run scripts through `env:`. The only `${{ }}` expressions sit in `if:`, `with:`, `name:` and `env:`. Expansions are quoted and the args are bash arrays.
- Tag families: the prefix checks in next_release_version.newest_tag and release_notes.previous_tag (an anchored regex on `git tag --list prefix*`) never mix the two families. release-tag's matrix compares each package's own version source. The before-commit read for kmaudit with no VERSION gives an empty OLD, which compares as skip, so the push that lands this releases nothing. Release commits and release PR merges of either family are skipped in both the notes and the late-commit list.
- Docs: the ADR 0012 correction and the overview match the workflows. The .loop/ differences against agent-audit are agent-audit's newer commits, not part of this change (the merge base is e039e047).

## Findings

- f1 (hardening, non-blocking): `PARENTS[2]^` is wrong only when the release branch's last commit sits on top of an update-from-main merge. In that case the warning is silently missing, so the published notes are still the reviewed ones. The plan prescribes this exact heuristic, so this is hardening, not a contract breach.
- f2 (docs, non-blocking): reword the module docstring line about the `v*` range so it says "the family's previous tag" and covers `--ref`, and fix the owns() docstring.

## Notes

`release.py set --package kmaudit` pins only the README. The install hints in packages/kmaudit/src/kmaudit/steps.py and packages/kmaudit/docs/commands.md still point at main. The plan's O2 names only the README, so this does not block. But a released kmaudit will tell users to install from main, unlike kmctl's pinned hook hints, so a follow-up ticket should cover it.
