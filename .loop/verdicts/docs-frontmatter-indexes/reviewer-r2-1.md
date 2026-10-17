---
type: verdict
title: 'Verdict: docs-frontmatter-indexes reviewer round 2'
description: 'reviewer verdict for round 2 of docs-frontmatter-indexes: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T17:16:16+00:00'
slug: docs-frontmatter-indexes
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f3 is fixed. The tutorial now says its commands ran with the kmctl release the page ships with. That holds because `scripts/release.py set` re-pins the tutorial's install line to each release tag (it is in `DOC_FILES`). The README hook snippet no longer pins `v0.3.0`, a tag that has no `.pre-commit-hooks.yaml`. It uses a `vX.Y.Z` placeholder, the same style the how-to pages use for `ref:`. One small new issue: the comment on that line will go stale (f4). It does not block.

## Checked

- `loopctl gate stamp` from the worktree: "stamp green: bec26f4a7de893e9e15039c12af80ddecef86f937f20547f492b50e52d137cc9". Lint, tests and integration passed, and so did rows r1-r9 and r11-r13.
- `docs/tutorials/get-started-with-kmctl.md` lines 1-30. Line 14 now reads "with the kmctl release this page ships with". The install line on line 22 is still `@v0.3.0`, and `release.py set` rewrites it through `_INSTALL`, so at each release the page names the release that was actually run.
- `git diff main -- README.md`. The `rev: vX.Y.Z` placeholder does not match `_INSTALL`, `_USES` or `_APM_PIN`, so `release.py set` leaves it alone and its `DOC_LINES` count of 6 is unchanged. The release tests passed in the stamp. `.pre-commit-hooks.yaml` defines `kmctl-check`, the id the snippet uses.

## Findings

- f1: resolved in round 1. The rule no longer says "lists every page".
- f2: resolved in round 1.
- f3: resolved at docs/tutorials/get-started-with-kmctl.md:14. The line no longer names a version that predates `check --fix`.
- f4: the README.md:209 comment "the hook ships from the next release" is true now, but becomes false once that release is out, and `release.py` will not touch it. Something like "the hook needs kmctl 0.4.0 or later" (or whatever the first release with `.pre-commit-hooks.yaml` will be) would stay true. A plain fix is enough; it does not need to come back to me.
