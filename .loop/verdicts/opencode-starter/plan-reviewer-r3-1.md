---
type: verdict
title: 'Verdict: opencode-starter plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of opencode-starter: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T06:02:02+00:00'
slug: opencode-starter
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p1 is resolved, and nothing else I checked could break the plan. It passes.

## Checked

- **Tags.** The local clone now has v0.1.0, v0.1.1, v0.2.0 and v0.2.1, and v0.2.1 is the highest. v0.3.0 sorts above it, so `uvx copier copy gh:JasperHG90/kmctl-starter` will render v0.3.0. v0.2.1 is a lightweight tag (`git cat-file -t` gives `commit`). Its release has one line of notes ("Fixes the description of `just upgrade` in `just --list`."). A plain tag plus a one-line release matches what is already there. A new harness choice as a minor bump also fits v0.2.0, which added `just upgrade`.
- **kmctl v0.5.1.** `gh release list -R JasperHG90/kmctl` shows v0.5.1 as Latest. The plan's condition for pushing is met, so bump-kmctl.yml will not open a PR that moves the default somewhere else, and test.yml on main will run against v0.5.1.
- **Starter files.** copier.yml's `harnesses` choices, the `kmctl_ref` validator (a regex today, which a version check can sit beside in Jinja), test.yml's matrix and doctor filter, README.md:11 and :34, and template/README.md.jinja are all where the plan says. Nothing in them conflicts with the plan.

## Findings

- p1 (premise, resolved): the plan tags v0.3.0, which sorts above v0.2.1, so copier renders it and offers OpenCode.
