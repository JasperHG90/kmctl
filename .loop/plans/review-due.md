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

It also lists handoffs past their `stale_after`. In a shallow clone, the history reason is skipped and the output says so; kmctl never guesses from partial history. Text by default, `--json` for scripts and the CI action, exit 0 whether or not anything is due. The logic is a function the briefing and the CI action call, not only a command body.

Done when tests cover each reason on a fixture bundle in a temporary git repository.

From planning: OKF `sources` entries may name URLs or concept ids as well as repository files. The git check applies only to repository paths, and the plan assumes they can be told apart reliably. Settled by spike:review-due/1: in the larger loop-harness bundle, 11 sources entries were 2 URLs, 2 tracked repository paths and 7 path-like entries naming files git does not track. A URL scheme and `git ls-files` never overlapped. So kmctl runs the git check only on entries `git ls-files` lists, skips URLs, and reports any other entry as its own reason, "source not found", instead of skipping it silently.

## Could invalidate this plan

- none
