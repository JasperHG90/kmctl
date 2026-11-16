---
type: plan
title: 'Plan: decision-candidates'
description: A new verb, kmctl decision candidates, lists with no model and without writing anything the changes since the newest decision record that may hold an unrecorded decision, each with what a judge needs, ordered by decision-shaped signals; ADR 0047 records the design.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T16:02:04+00:00'
slug: decision-candidates
epic: null
depends_on:
- decision-gaps-measure
priority: null
schema_version: '2.0'
---

# decision-candidates

Relayed from: none

## Intent

The operator wants kmctl to find changes in git history that made a
decision nobody recorded, report them, and leave it to the user to turn
any into records. `.okf/prototypes/decision-gaps/` measured the approach on
this repository: an agent judging every change found 25 of 30 hidden
decisions for about two cents a change, and cutting by a no-model score
would have lost one in six. ADR 0046 puts the scan in kmctl. The operator
named the verb: a command that only lists changes must not promise gaps.

This ticket builds the no-model half: `kmctl decision candidates`, in
`new:packages/kmctl/src/kmctl/candidates.py` and the `decision` group of
`packages/kmctl/src/kmctl/__init__.py`. It:

- reads history from `--since REF`, by default the commit that added the
  newest decision record (the whole history when there is none), up to
  `HEAD`;
- splits it into changes the way the prototype's `units.py` does: one per
  ticket merge, pull request or plain commit, syncs and ticket-carrying
  pull requests expanded, loop state, release and placeholder commits left
  out;
- gives each change its sha, first parent, kind, subject, message, ticket
  slug and plan path when the ticket has a plan under .loop/plans/, changed
  files, the decision records it added or amended (so a judge sees it is
  already recorded), the decision-shaped signals and their score;
- lists every change, highest score first, as a table by default and as
  JSON with `--json`, writes nothing and calls no model, and refuses with
  a fix line outside a git repository or for a `--since` that names no
  commit.

`new:.okf/decisions/0047-unrecorded-decisions-are-listed-by-kmctl-and-judged-by-a-skill-that-only-reports.md`
records the design: the command lists, a skill judges every change and
reports, the user decides what becomes a record; rejected are cutting by
score (the measurement), a skill reading raw `git log` (splitting merges is
easy to get wrong), and writing records automatically (precision near
60%). `docs/reference/commands.md` documents the verb. The skill is the
next ticket, `decision-gaps-skill`.

It worked when, in a test repository with ticket merges, a ticket-carrying
pull request, a sync, plain commits and noise, the verb lists exactly the
expected changes with their recorded and score fields, and its help passes
the help tests.

## Problems

- P1: kmctl cannot list the changes since the last decision record in a form an agent can judge.

## Goals

- G1: An agent can review a repository's history for unrecorded decisions from one kmctl command's output.

## Outcomes

### O1: kmctl decision candidates lists the changes since the newest decision with what a judge needs
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:packages/kmctl/src/kmctl/candidates.py`, `packages/kmctl/src/kmctl/__init__.py`, `new:packages/kmctl/tests/test_candidates.py`, `docs/reference/commands.md`, `new:.okf/decisions/0047-unrecorded-decisions-are-listed-by-kmctl-and-judged-by-a-skill-that-only-reports.md`, `.okf/decisions/index.md`, `.okf/log.md`, `.okf/summary.md`
- checked by: tests on temporary git repositories for the split (ticket merges, a pull request carrying tickets, a pull request without, a sync, plain commits, skipped noise), the default and explicit --since, the recorded field for added and amended records, the plan path, score ordering, the JSON shape, the refusals, and that nothing is written; the help tests; kmctl check
- seen by: calling code

## Could invalidate this plan

- none
