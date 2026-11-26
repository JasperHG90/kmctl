---
type: verdict
title: 'Verdict: okf-vs-change-audit-reviewer-f3 plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of okf-vs-change-audit-reviewer-f3: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-26T22:18:54+00:00'
slug: okf-vs-change-audit-reviewer-f3
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works. Matching only bot-written comments fixes f3 for the action, which always publishes with `github.token`. One contract gap is open (p1): run by hand with a non-bot token, `publish --pr` would add a new comment on every run.

## Checked

Checked against the code on main.

**Is `user.type == "Bot"` the right test?** Yes, for the action. The REST
issue-comment object carries `user.login` and `user.type`. A comment written
with `GITHUB_TOKEN` comes from `github-actions[bot]` with type `Bot`. A
GitHub App installation token posts as `<app>[bot]`, also type `Bot`. A
person's comment is type `User`, so the f3 failure (PATCH on a person's
comment, exit 1 on every push) goes away. The publish step always runs with
`github.token` (action.yml:272), so the action's own path is covered. The
gap is the CLI used with a non-bot token (p1).

**Another bot quoting the marker.** Under O1, another bot whose comment
holds the marker (a summary bot that quotes the thread, say) would still be
picked first, and the PATCH would fail as in f3. That is much narrower than
a person quoting it: the marker is an HTML comment, so it does not show in
the rendered thread and only gets copied from the raw source. Two kmctl
workflows with the same title both post as github-actions[bot], which can
edit its own comments, so that case works. I do not count this as a
finding. If the plan wants to close it cheaply, it could also require the
comment body to start with the marker, which is how `publish_comment`
writes it (`f"{mark}\n## ..."`). A quote nests inside `> ` and would not
match.

**O2.** The how-to (docs/how-to/install-the-plugin-and-the-ci-action.md:466-476)
says the publish job "keeps `!cancelled()` too", but the single-audit
workflow it tells you to copy has no such condition. Only the matrix variant
(line 430) and this repo's workflow (.github/workflows/knowledge-audit.yml:79)
have it. The fix is a docs sentence. r3 checks it.

**Facts vs prose.** P1/P2 are separate causes. O1 is a behaviour that can
ship alone, and O2 is support. Needs and touches match the prose, except
that p1 may add the help text to O1's scope. The existing replace test
(r2) will need `user` fields in its fake-gh fixtures. O1 already touches
tests/test_agent.py, so that is just building work.

## Findings

- p1: the bot-only test breaks the one-comment promise in `publish --pr`'s help for a person's or machine user's token. See front matter.

## Notes

No spike needed. The plan lists no risks under "Could invalidate this
plan", and none is missing that would invalidate it.
