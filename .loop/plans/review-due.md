---
type: plan
title: 'Plan: review-due'
description: "kmctl review due lists the concepts due for review from OKF's own fields and the expired handoffs (ADR 0006)."
slug: review-due
epic: cli
depends_on: []
priority: 3
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:19+00:00'
---

# review-due

Relayed from: none

## Intent

`kmctl review due` lists concepts in `.okf/` that are due for review, each with its reason (ADR 0006):

- `stale_after` has passed;
- no `verified` entry;
- a file in its `sources` changed in git after its last `verified` date.

It also lists handoffs past their `stale_after`. Text by default, `--json` for scripts and the CI action, exit 0 whether or not anything is due. The logic is a function the briefing and the CI action call, not only a command body.

Done when tests cover each reason on a fixture bundle in a temporary git repository.

## Could invalidate this plan

- OKF `sources` entries may name URLs or concept ids as well as repository files. The git check applies only to repository paths, and the plan assumes they can be told apart reliably.
