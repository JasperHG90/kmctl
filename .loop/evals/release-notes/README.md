---
type: eval
title: 'Eval: release-notes'
description: 'Definition of done for release-notes: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.1.dev16+g27435b040.d20261017
  at: '2026-10-19T12:50:31+00:00'
slug: release-notes
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: 4459f13e449ab550ca16f36dfd74abe7f1f31b65a4bb7d38d05b794e97d165d0
  at: '2026-10-19T12:50:31+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: scripts/release_notes.py lists each Merge loop/SLUG: SUMMARY on main's first-parent history between the previous tag and the given tag under Changes, and each other commit under Other changes.
  Fails when: a loop merge in the range is missing from Changes or lands under Other changes, a plain commit is missing from Other changes, or a commit outside the range appears
- r2: The notes leave out loop: state commits, release: commits, release pull request merges, Merge remote-tracking branch, merges of main into a branch, and operator: manual / chore; manual placeholder commits.
  Fails when: any of those subjects appears in the printed notes
- r3: The notes come from .github/release-notes.md filled with the version, an install line pinned to the tag, and a compare link to the previous tag; the first release has no compare link; an unknown tag exits nonzero naming it.
  Fails when: the output lacks the template's headings, the install line does not name vVERSION, the compare link names the wrong previous tag or appears for the first release, or an unknown tag exits 0
- r4: release-tag.yml writes the notes with scripts/release_notes.py and publishes with --notes-file, not --generate-notes.
  Fails when: release-tag.yml contains --generate-notes, or its publish step does not pass a notes file produced by scripts/release_notes.py
- r5: On this repository, the script's notes for v0.10.0 list drop-summary-nudge under Changes and the uv cache commit under Other changes, with no loop: or release: lines.
  Fails when: drop-summary-nudge is missing, the uv cache commit is missing, or a line starts with loop: or release:
- r6: ADR 0012 says where the release notes come from.
  Fails when: ADR 0012 does not name scripts/release_notes.py
