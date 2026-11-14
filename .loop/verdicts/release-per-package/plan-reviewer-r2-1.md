---
type: verdict
title: 'Verdict: release-per-package plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of release-per-package: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:54:27+00:00'
slug: release-per-package
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three round 1 findings are closed, and nothing new could break the plan. The outcomes now cover the late-commit check: O4 writes the trailer and O5 reads it. The drafted commit now lives in git history and in a commit trailer, not in the file Hermes rewrites. kmaudit's VERSION file starts at a .dev version that compare skips.

## Checked

- scripts/release.py compare: a .dev new version returns skip before the empty-OLD branch, so `compare '' 0.1.0.dev0` gives skip as O1 says.
- scripts/next_release_version.py: with no tag in the family it refuses unless --version is given, so kmaudit's first release has to be 0.1.0 typed by hand. That matches the prose.
- release.yml: bump already runs on the run's checkout (GITHUB_SHA). Putting the draft in a separate notes job that runs in dry runs and passes an artifact to bump fits the current job layout. release-notes-hermes puts its step in that same job, between the draft and the notes file, and its cleaning strips HTML comments and trailers only from Hermes' reply. The Drafted-From trailer sits in the commit message and the pull request body, not in the notes file, so the rewrite cannot remove it.
- Merge shapes: a merge commit gives MERGE^2^1 = the drafted commit. A squash or rebase merge leaves one parent, and the pushed commit's message carries the trailer: a rebase keeps the bump commit's message, and a squash carries either that message or the pull request body, both of which hold it. If someone clicks "Update branch" on the version pull request, MERGE^2^1 is the bump commit, not the drafted commit. The range bump..MERGE^1 still lists exactly the late commits, because the bump commit has none of them as ancestors, so the result stays right.
- Problems, goals and outcomes: O4 and O5 now list what the prose describes (the notes job, the artifact, the trailer, finding the drafted commit, the warning). O1 lists the .dev start. The needs chain O1 -> O2 -> O3 -> O4 -> O5 matches what each step uses. O4 and O5 are the behaviours that ship; O1 to O3 are support.
- Eval rows: r1 tests the .dev start and the skip, r4 tests the notes job in dry runs, the artifact handoff, building on the drafted commit and the trailer in both places, and r5 tests both ways of finding the drafted commit and the late-commit warning. Each row checks what its outcome claims.

## Findings

- p1 (resolved): O4 and O5 now cover the late-commit check, and r4 and r5 test it.
- p2 (resolved): the drafted commit lives in git history and a commit trailer, which the Hermes rewrite cannot touch.
- p3 (resolved): VERSION starts at 0.1.0.dev0, which compare skips, so the push that lands this ticket releases nothing.

## Notes

- Not a finding: finding the drafted commit from the trailer works for every merge shape. The two-parent path is a second route to the same answer, and the build can keep or drop it.
