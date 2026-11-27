---
type: verdict
title: 'Verdict: okf-vs-change-audit-reviewer-f3 reviewer round 1'
description: 'reviewer verdict for round 1 of okf-vs-change-audit-reviewer-f3: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-26T22:31:48+00:00'
slug: okf-vs-change-audit-reviewer-f3
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `publish_comment` now takes a comment as its own only when the body starts with the marker, so a person who quotes the marker under `> ` is left alone. The new test would fail on the old code. The how-to sentence now tells the reader to add `!cancelled()` instead of saying the job keeps it. The stamp is green.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree. All four gates passed (lint, format, tests, integration), and so did eval rows r1 to r4. The stamp is green with fingerprint 493bc4e6...c843c, the same one the round binds.
- Every body publish writes still matches. `publish_comment` builds every body as `f"{mark}\n## {title}\n\n..."`. That covers both the findings body and the "found nothing" body, for both POST (`gh pr comment --body-file`) and PATCH (`gh api -F body=@file`). The `-F @file` form sends the file as it is. `git log -S'kmctl-audit:'` shows the marker arrived in dd6b5184, and no tag contains that commit, so no released version wrote a body in another shape that would stop matching now.
- Does GitHub change how a body starts? The REST API returns the body as stored. GitHub adds no BOM and does not trim or rewrite HTML comments in the raw body. It may turn line endings into CRLF when someone edits in the web UI, but the marker holds no newline, so `startswith` still matches. The marker ends in ` -->`, so a title that extends another (for example "Knowledge audit 2") cannot match by prefix.
- Row r1: `test_publish_pr_ignores_a_person_quoting_the_marker` seeds a quoted-marker comment and publishes twice. It then asserts that the person's comment is unchanged, that there are exactly two comments (so the second run replaced its own comment instead of posting a third), and that the new comment starts with the marker. On the old code, the first run would have PATCHed comment 1, and the first assert fails. This covers both halves of `fails_when`.
- Row r2: the existing create-then-replace test is unchanged and passes.
- Row r3: I read the sentence in context. The single-audit workflow it copies has no `if:` on publish, and the snippet below the sentence shows the `!cancelled() && ...` condition, so the new wording is correct.
- Consistency: ADR 0057, `.okf/architecture/` and the `publish` help never say how the earlier comment is found, so none of them is now false. The new code comment is accurate.
- The `git diff --cached main` output also shows `.loop/` state differences. They come from main moving on, not from this change, so I ignored them.

## Findings

None.
