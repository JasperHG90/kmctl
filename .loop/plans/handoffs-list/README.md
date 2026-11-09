---
type: plan
title: 'Plan: handoffs-list'
description: "kmctl handoffs lists the live handoffs in .okf/handoffs/, newest first, for the briefing and /continue."
slug: handoffs-list
epic: cli
depends_on: []
priority: 2
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:21:23+00:00'
---

# handoffs-list

Relayed from: none

## Intent

`kmctl handoffs` lists the handoffs in `.okf/handoffs/` whose `stale_after` has not passed, newest first by `generated.at` (ties broken by file name), with concept id, path, title, description and date, so `/continue` can load the ones the user picks. The section's `index.md` is not a handoff. "Passed" uses one shared function with review-due, so a handoff is always in exactly one of the two lists. Expired ones are left out (`kmctl review due` lists them). The list is a function the briefing calls; `--json` prints it for `/continue`. With no `.okf/handoffs/` folder it prints that there are none (`[]` with `--json`) and exits 0.

Done when tests cover ordering, leaving out expired handoffs, a handoff with no `stale_after` (listed as live), a tie on `generated.at`, the `index.md` being skipped, path and id in the JSON, and a repository with no handoffs folder.

## Could invalidate this plan

- none
