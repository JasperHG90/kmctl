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

Adds a link check to `kmctl check`: every relative markdown link in `docs/` and `.okf/` points at a file that exists (anchors are not checked). Each broken link is reported with its file and line.

Done when tests cover a passing and a failing fixture.

## Could invalidate this plan

- none
