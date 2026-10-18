---
type: verdict
title: 'Verdict: verify-verb-reviewer-f6 plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of verify-verb-reviewer-f6: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T21:48:29+00:00'
slug: verify-verb-reviewer-f6
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The defect reproduces: with docs/ a symlink to a folder outside the repository, `kmctl review due` lists `docs/sub/p` while `verify` on that id raises ValueError at `path.relative_to(root.resolve())`. Naming the page from its repository spelling (as `_target` already builds `shown`) instead of from the resolved path is a local fix. No risk found that could break the plan.

## Checked

- src/kmctl/verify.py line 166: `rel = path.relative_to(root.resolve()).as_posix()`; `_target` resolves the base folder, so the path lies outside root when docs/ or .okf/ links out.
- src/kmctl/review_due.py `_docs_due` and the concept loop name pages with `path.relative_to(root)` on unresolved paths from `root / "docs"`, so they print `docs/...` and `.okf/...` names.
- Scratch repo with docs -> outside folder and a page with a passed stale_after: review due lists `docs/sub/p`; verify raises ValueError.
- `append_log` writes to `root / ".okf" / "log.md"`, which follows the symlink, so a symlinked .okf/ needs no other change.
- Eval r1 picks writing over refusing, which matches review due listing those pages; its fails_when matches.

## Findings

None.

## Notes

A symlink nested inside docs/ that points out of it is still refused by `_target`'s is_relative_to check; that is outside this ticket.
