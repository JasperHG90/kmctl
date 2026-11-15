---
type: eval
title: 'Eval: kmaudit-install-hints-pinned'
description: 'Definition of done for kmaudit-install-hints-pinned: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:46:31+00:00'
slug: kmaudit-install-hints-pinned
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: a048e0b5c439ed519c4f1fdf5f7eec5e41f61d78bd743c412389cf3ee68784af
  at: '2026-11-15T05:46:31+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit builds its install hint from its installed version: a release or pre-release version names its kmaudit-vX.Y.Z tag with #subdirectory=packages/kmaudit, a dev or local version names no ref, and extras go in the requirement, so the tracing refusal asks for kmaudit[tracing]; steps.py, judge.py, check_verbs.py and ui.py use it.
  Fails when: a release version's hint lacks its tag, a dev version's names one, the tracing refusal leaves out the extra, or a hand-written INSTALL string remains
- r2: release.py set --package kmaudit pins kmaudit's README install line and the tracing line in packages/kmaudit/docs/commands.md to the release tag, and refuses, writing nothing, when either line is missing; the Release run's kmaudit bump stages docs/commands.md.
  Fails when: either line keeps an old ref, a missing line is not refused or something is written anyway, or the bump leaves docs/commands.md out
