---
type: plan
title: 'Plan: okf-vs-change-audit-reviewer-f3'
description: Deferred hardening from okf-vs-change-audit, reviewer finding f3 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T21:37:12+00:00'
slug: okf-vs-change-audit-reviewer-f3
epic: null
depends_on: []
priority: null
schema_version: '2.0'
---

# okf-vs-change-audit-reviewer-f3

Relayed from: okf-vs-change-audit, reviewer finding f3 in review round 1

## Intent

`publish_comment` in `action/agent.py` takes the first pull request comment
whose body holds the audit's marker, from any author. A person who quotes
the marker, say to discuss a finding, makes every later publish PATCH that
person's comment, which `GITHUB_TOKEN` cannot edit, so publish exits 1 on
every push. Match only a comment whose body starts with the marker, which
is how `publish_comment` writes its own (`f"{mark}\n## ..."`). A quote
nests the marker under `> `, so it never matches. This keeps working with
any token that posts the comment: `GITHUB_TOKEN` (`github-actions[bot]`), a
GitHub App, or a person's or machine user's own token, whose comments are
type `User`; matching on `user.type == "Bot"` would break `--pr` for the
last two, which the `publish` help promises only need `gh` and `GH_TOKEN`.

The same ticket fixes one sentence in
`docs/how-to/install-the-plugin-and-the-ci-action.md`: its pull request part
says the publish job "keeps `!cancelled()` too", but the single-audit
workflow it copies has no such condition; only the matrix version does.

Measured effect: none from history, since the comment is new in
okf-vs-change-audit. One quoted marker is enough to make publish fail on
every later push of that pull request, which review round 1 of
okf-vs-change-audit showed from the code.

## Problems

- P1: `publish_comment` treats a person's comment that quotes the marker as its own, so publish fails on every later push.
- P2: The how-to's pull request part says the publish job keeps a `!cancelled()` condition that the workflow it copies does not have.

## Goals

- G1: Publish keeps one comment per pull request whatever people write beside it, and the how-to says what to copy.

## Outcomes

### O1: Publish replaces only a comment that starts with its marker
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `action/agent.py`, `tests/test_agent.py`
- checked by: a test with a fake `gh` where a person's comment quotes the marker: publish leaves it alone, posts its own comment, and replaces that one on the next run; the existing replace test still passes
- seen by: operator

### O2: The how-to's pull request part says to add `!cancelled()` to publish, not that it is kept
- kind: support
- goal: G1
- fixes: P2
- needs: none
- touches: `docs/how-to/install-the-plugin-and-the-ci-action.md`
- checked by: an eval row that the sentence no longer says "keeps `!cancelled()` too"
- seen by: operator

## Could invalidate this plan

- none
