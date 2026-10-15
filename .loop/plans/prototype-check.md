---
type: plan
title: 'Plan: prototype-check'
description: "kmctl check also fails when a folder under .okf/prototypes/ has no README.md."
slug: prototype-check
epic: cli
depends_on: [knowledge-check]
priority: 6
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:07:38+00:00'
---

# prototype-check

Relayed from: none

## Intent

Adds a prototype check to `kmctl check`: every folder directly under `.okf/prototypes/` has a `README.md` concept. Folders nested deeper (a prototype's `src/` or `results/`) are not prototypes and are not checked.

Done when tests cover a passing fixture, a passing fixture whose prototype has a nested folder with no `README.md`, and a failing fixture.

## Could invalidate this plan

- none
