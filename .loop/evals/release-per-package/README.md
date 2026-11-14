---
type: eval
title: 'Eval: release-per-package'
description: 'Definition of done for release-per-package: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:47:13+00:00'
slug: release-per-package
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: d2d0d0001fbcf6b9c332d52a2e3873a8edb044e2367e5ee81077c12acc1e71f0
  at: '2026-11-14T17:47:13+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit's version comes from packages/kmaudit/VERSION through hatchling's regex source, and `release.py --package kmaudit current` prints it.
  Fails when: the pyproject keeps a static version, the VERSION file is not read, or current prints something else
- r2: next_release_version.py, release.py, check_wheel.py and smoke_wheel.py take --package: kmaudit reads only kmaudit-v* tags and writes only its VERSION file and README install line; kmctl behaves as today.
  Fails when: a package reads the other family's tags, set touches the other package's files, or kmctl's behaviour changes
- r3: release_notes.py --package P TAG --ref HEAD --out FILE drafts notes for an unpushed tag from the family's previous tag, listing only commits that touch that package's paths.
  Fails when: it refuses an unpushed tag, starts from the other family's tag, or lists a commit that touches only the other package
- r4: The Release run takes package (kmctl, kmaudit), drafts the notes to .github/release-notes/TAG.md before the bump step, commits that file in the version pull request and uses it as the body.
  Fails when: the package input is missing, the draft step is absent or after bump, or the file is not committed or not the body
- r5: release-tag triggers on apm/apm.yml and packages/kmaudit/VERSION, refuses before tagging when the committed notes file is missing or blank, publishes exactly that file, warns naming commits that landed after the draft, and marks only kmctl Latest.
  Fails when: a path is missing, the refusal runs after git tag -a or not at all, notes come from anywhere else, late commits are not named, or kmaudit is marked Latest
