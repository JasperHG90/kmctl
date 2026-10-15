---
type: plan
title: 'Plan: ci-action'
description: "A reusable GitHub Action that runs kmctl check and kmctl review due on every pull request, at no model cost (ADR 0005)."
slug: ci-action
epic: ci
depends_on: [knowledge-check, review-due]
priority: 10
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:23+00:00'
---

# ci-action

Relayed from: none

## Intent

Adds `new:action.yml`, a composite action that installs kmctl from the action's own checkout, runs `kmctl check` and `kmctl review due --json`, writes both to the job summary, and fails only on `kmctl check`.

The review-due reason "a source changed after the last verified date" reads git history, and `actions/checkout` fetches one commit by default. The action deepens the clone itself (`git fetch --unshallow` when the repository is shallow) and, if that fails, says in the summary that the history-based reason was skipped. It never guesses from a shallow clone.

The action's steps live in one script the action runs, so the loop can test them locally. A workflow for this repository under .github/workflows/ uses the action on itself. Its first run on GitHub is the operator's to watch after the merge; it is not part of done.

Done when tests run the script against a fixture repository and show: it exits 0 and writes both reports when `kmctl check` passes, exits nonzero when `kmctl check` fails, exits 0 when concepts are due, and deepens a shallow clone (made with `git clone --depth 1`) before reading history.

## Could invalidate this plan

- none
