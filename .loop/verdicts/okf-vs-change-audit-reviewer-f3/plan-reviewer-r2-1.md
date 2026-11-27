---
type: verdict
title: 'Verdict: okf-vs-change-audit-reviewer-f3 plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of okf-vs-change-audit-reviewer-f3: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-26T22:19:58+00:00'
slug: okf-vs-change-audit-reviewer-f3
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The revised plan works. Matching a comment whose body starts with the marker fixes f3 with any token, so p1 is resolved. No open risk could break the plan.

## Checked

`publish_comment` (action/agent.py:1013-1070) finds the earlier comment with `mark in body` at line 1034 and always writes its own body as `f"{mark}\n## {title}\n\n..."` (line 1041), sent through `gh pr comment --body-file` or a PATCH with `body=@file`. Neither adds leading text, so every comment the tool has posted, including ones from before this change, starts with the marker and keeps matching. A quote puts `> ` before the marker, and a person mentioning it mid-sentence puts other text first, so neither matches. GitHub may store line endings as CRLF, but that does not affect a prefix test. The marker ends in ` -->`, so one title cannot be a prefix match of another.

The only remaining false match is a person whose comment starts with the raw HTML-comment marker. The marker does not show in the rendered thread, so this is a deliberate copy of the raw source and far narrower than f3. It is not worth a finding.

The `--pr` help (agent.py:1386) promises one comment, replaced on the next run. That stays true for any token, so the help needs no change. The existing replace test's fake `gh` stores the body file as written, so r2 keeps passing without fixture changes. r1 names the new test O1 describes.

O2 has not changed since round 1, which checked it against the how-to and the workflows. r3 checks the sentence is gone.

Facts against prose: P1 and P2 are separate causes. O1 is a behaviour that can ship alone, and O2 is support. Neither waits on the other, so `needs: none` is right. Touches cover what the prose changes.

## Findings

- p1: resolved. The plan dropped the `user.type == "Bot"` test for a starts-with-marker test, which keeps `publish --pr` working with any token.

## Notes

No spike is needed. "Could invalidate this plan" lists none, and I found no unlisted risk.
