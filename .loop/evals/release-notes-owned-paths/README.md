---
type: eval
title: 'Eval: release-notes-owned-paths'
description: 'Definition of done for release-notes-owned-paths: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:35:15+00:00'
slug: release-notes-owned-paths
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 4b731d1706a8398df08a9d1bc99e090f8a5190432bee707e6221b1bc0d9887cb
  at: '2026-11-15T05:35:15+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: scripts/release_paths.py's owns gives no package .loop/, .okf/, .claude/ or uv.lock; kmaudit owns packages/kmaudit/, kmctl packages/kmctl/ and every other path outside packages/; its command reads paths on stdin and exits 0 when the package owns any of them, else 1.
  Fails when: a bookkeeping path counts for either package, a shipped path is not owned by its package, or the command's exit code disagrees with owns
- r2: release_notes.py takes owns from release_paths.py: a commit touching only .okf/ and uv.lock is in neither package's notes, one touching .okf/ and packages/kmaudit/ is in kmaudit's, one touching .claude/ and docs/ is in kmctl's, and every earlier release_notes test passes.
  Fails when: a bookkeeping-only commit is listed, a mixed commit is left out of its package's notes, or any release_notes test fails
- r3: release-tag's late-commit step decides ownership by piping each late commit's paths to release_paths.py, holds no awk copy of the rule, does not name a late bookkeeping-only commit but names a late shipped one, and still never runs release_notes.py or --generate-notes.
  Fails when: the step keeps an awk ownership rule, names a bookkeeping-only commit, misses a shipped one, or release-tag.yml names release_notes.py
