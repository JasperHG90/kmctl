---
type: plan
title: 'Plan: review-due'
description: "kmctl review due lists the concepts due for review from OKF's own fields and the expired handoffs (ADR 0006)."
slug: review-due
epic: cli
depends_on: []
priority: 2
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

Each `sources[].resource` is resolved the way OKF §6.2 says, then checked against `git ls-files`: an absolute URL is skipped; a path starting with `/` resolves from the bundle root; another path resolves from the concept's own folder, and, when that does not exist, from the repository root, because real bundles use repository-root paths (spike:review-due/1). A source that names another concept resolves to that concept's file. An entry that resolves to no tracked file, such as a free-text scope descriptor (§5.1), is not a due reason: it is listed separately as a notice, "source not resolved", so it never keeps a concept due for good.

It also lists handoffs past their `stale_after`.

In a shallow clone, the history reason is skipped and the output says so; kmctl never guesses from partial history. Text by default, `--json` for scripts and the CI action, exit 0 whether or not anything is due. The logic is a function the briefing and the CI action call, not only a command body.

Done when tests cover each due reason and each source form (URL, bundle-root, concept-relative, repository-root, concept id, free text) on a fixture bundle in a temporary git repository, and the shallow-clone skip.

## Could invalidate this plan

- none
