---
type: eval
title: 'Eval: release-per-package'
description: 'Definition of done for release-per-package: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:53:11+00:00'
slug: release-per-package
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 26196799b50bca34b5d76f297adfeb015410d898b1659a74ccc7b1cd52a4af52
  at: '2026-11-14T17:53:11+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit's version comes from packages/kmaudit/VERSION through hatchling's regex source and starts at 0.1.0.dev0; `release.py --package kmaudit current` prints it, and `release.py compare '' 0.1.0.dev0` prints skip, so the push that adds the file releases nothing.
  Fails when: the pyproject keeps a static version, the VERSION file is not read, or current prints something else, or the file starts at a releasable version, or compare does not skip it
- r2: next_release_version.py, release.py, check_wheel.py and smoke_wheel.py take --package: kmaudit reads only kmaudit-v* tags and writes only its VERSION file and README install line; kmctl behaves as today.
  Fails when: a package reads the other family's tags, set touches the other package's files, or kmctl's behaviour changes
- r3: release_notes.py --package P TAG --ref HEAD --out FILE drafts notes for an unpushed tag from the family's previous tag, listing only commits that touch that package's paths.
  Fails when: it refuses an unpushed tag, starts from the other family's tag, or lists a commit that touches only the other package, or kmaudit's first draft (no kmaudit-v* tag) leaves out an earlier commit that touched packages/kmaudit/
- r4: The Release run takes package (kmctl, kmaudit). A notes job that also runs in dry runs drafts .github/release-notes/TAG.md and uploads it as an artifact; bump downloads it, commits it on top of the drafted commit with a `Drafted-From: <sha>` trailer, and opens the version pull request with a body holding the notes and the trailer.
  Fails when: the package input is missing, the draft job is skipped in a dry run or does not hand the file to bump, bump does not build on the drafted commit, the trailer is missing from the commit or the body, or the file is not committed or not the body
- r5: release-tag triggers on apm/apm.yml and packages/kmaudit/VERSION, refuses before tagging when the committed notes file is missing or blank, and publishes exactly that file; it finds the drafted commit from the merge's second parent, or from the Drafted-From trailer on a squash merge, and writes a ::warning:: and a step-summary section naming package commits that landed after it; only kmctl is marked Latest.
  Fails when: a path is missing, the refusal runs after git tag -a or not at all, notes come from anywhere else or the published file differs from the reviewed one, the drafted commit is not found for a merge or a squash, late commits are not named, or kmaudit is marked Latest
