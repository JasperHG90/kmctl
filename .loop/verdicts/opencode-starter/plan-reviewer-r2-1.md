---
type: verdict
title: 'Verdict: opencode-starter plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of opencode-starter: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T05:59:34+00:00'
slug: opencode-starter
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

One premise is wrong, and it breaks the tagging step. kmctl-starter's newest tag is v0.2.1, not v0.1.1, so v0.1.2 would never be the version copier renders. The rest of the plan holds, and the round 1 checks still apply.

## Checked

- **Existing tags.** `git ls-remote --tags origin` lists v0.1.0 (e0259a1), v0.1.1 (a5d01f9), v0.2.0 (212e4d5) and v0.2.1 (0dbec4c, equal to origin/main and the local HEAD). `gh release list -R JasperHG90/kmctl-starter` shows a GitHub release for each one, with v0.2.1 as Latest. All of them were published on 2026-10-18 between 04:37 and 04:51. Locally, `git cat-file -t` gives `commit` for v0.1.0 and v0.1.1, so they are lightweight tags. v0.2.x is not fetched into the local clone. The releases have short notes, for example v0.1.1: "`kmctl_ref` now defaults to kmctl v0.5.0". The pattern to follow is a lightweight tag plus a `gh release create` with one line of notes. Copier does not need the release, only the tag, but the new tag should match the others.
- **Workflows that react to tags.** There are none. test.yml runs on `pull_request`, `workflow_dispatch` and `push` to `branches: [main]` only. bump-kmctl.yml runs on a schedule and on `workflow_dispatch`. Pushing a tag starts nothing, and pushing main starts test.yml.
- **Order relative to kmctl v0.5.1.** `gh release list -R JasperHG90/kmctl` already shows v0.5.1 as Latest (published 05:58:34Z). The plan's precondition is met, so test.yml on main and bump-kmctl.yml will both see v0.5.1.
- **README floor.** README.md:11 still reads "It needs kmctl v0.4.0 or later". The plan's new item covers this.

## Findings

- p1 (premise, blocking): the plan tags v0.1.2, but v0.2.1 is already kmctl-starter's newest tag, so copier would still render v0.2.1 and nobody would get the OpenCode choice. Tag above v0.2.1 instead.

## Notes

- Run `git fetch --tags` in /home/vscode/kmctl-starter before tagging. Without it, any check of "newest tag" in the local clone gives the same wrong answer the plan got.
