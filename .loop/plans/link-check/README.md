---
type: plan
title: 'Plan: link-check'
description: "kmctl check also fails when a relative markdown link in docs/ or .okf/ does not resolve."
slug: link-check
epic: cli
depends_on: [knowledge-check]
priority: 6
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:07:36+00:00'
---

# link-check

Relayed from: none

## Intent

Adds a link check to `kmctl check` for the links the okf validator does not cover. The validator already checks links inside `.okf/` and only warns, because OKF §6.1 says tools must tolerate broken links there; kmctl leaves those to it.

kmctl checks, and fails on:

- every markdown link in `docs/`: a relative link resolves from the page's folder, and a link starting with `/` resolves from the repository root, as GitHub renders it;
- every relative link in `.okf/` that leaves the bundle (for example `../src/...`), resolved from the page's folder. Links starting with `/` in `.okf/` resolve from the bundle root (OKF §6.1) and stay inside it, so they are the validator's.

URLs and anchors are not checked. Each broken link is reported with its file and line.

Done when tests cover, for `docs/`, a passing and a failing relative link and a passing and a failing `/` link, and for `.okf/`, a passing and a failing link that leaves the bundle, plus a broken in-bundle link that `kmctl check` does not report.

## Could invalidate this plan

- none
