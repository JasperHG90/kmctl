---
type: plan
title: 'Plan: knowledge-check'
description: "kmctl check fails when an index disagrees with its folder in docs/ or an .okf/ section."
slug: knowledge-check
epic: cli
depends_on: []
priority: 6
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:21+00:00'
---

# knowledge-check

Relayed from: none

## Intent

`kmctl check` reports, with a non-zero exit when any fails, that every page under `docs/` and every concept in an `.okf/` section is listed in its index, and every index entry exists. `--json` for the CI action. It does not repeat what the okf validator checks. Later checks (links, prototypes) add to this command.

Done when tests cover a passing and a failing fixture for a missing entry and for an entry with no file.

## Could invalidate this plan

- none
