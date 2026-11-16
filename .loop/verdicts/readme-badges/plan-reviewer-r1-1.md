---
type: verdict
title: 'Verdict: readme-badges plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of readme-badges: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T09:07:48+00:00'
slug: readme-badges
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works and the scope fits one ticket. None of the plan's claims about the repo turned out wrong, and I found no unlisted risk that could break it. There is one fact mismatch: O2 claims it needs nothing, but its check depends on the lifecycle badges O1 adds, and plan.split acts on that field.

## Checked

- The plan has no listed risks, so there were no spike citations to check.
- tests/test_readmes.py: the root README must stay under 80 lines. It has 42 now, so a badge line and a few inline badges fit. The link check only looks at relative links. Absolute badge URLs are skipped, and a licence badge that links to a relative LICENSE still passes, because LICENSE exists at the root and in both packages.
- scripts/release.py: `set` rewrites install lines with regexes `_INSTALL`, `_HOOK_INSTALL` and `_KMAUDIT_INSTALL`. All of them match `git+https://github.com/JasperHG90/kmctl`, which shields.io and GitHub Actions badge URLs do not contain. So the release tooling will not rewrite or trip on badges in the kmaudit README or the command reference.
- scripts/check_wheel.py only checks package data files, not metadata. Nothing in the repo reads or pins classifiers, and neither pyproject has a classifiers list yet. Both Development Status strings are valid trove classifiers.
- .github/workflows/ci.yml runs on push to main, so a CI badge for main will show a status. The repo is public, so shields.io can read it.
- Releases: v0.13.0 is marked Latest, and kmaudit-v0.1.0 is a newer non-prerelease. An unfiltered release badge would be wrong, and the plan already filters by tag family. Shields matches the filter against the whole tag name, so `v*` does not match `kmaudit-v0.1.0`.
- Problems, Goals and Outcomes against the prose: every behaviour in the prose has an outcome, and each `touches` list covers the files the prose changes.

## Findings

- p1: O2's `needs: none` is wrong. Its check reads the lifecycle badges O1 adds, and the two outcomes edit the same files, so splitting them on these facts would produce a ticket that cannot pass on its own or two tickets that collide.

## Notes

Adding a sentence to docs/reference/kmaudit-commands.md may make kmaudit's stored claims for that section stale. That is expected upkeep, not a risk to the plan.
