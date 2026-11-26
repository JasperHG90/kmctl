---
type: plan
title: 'Plan: adr-0057-pr-audit'
description: Revise draft ADR 0057 on PR 71 so it builds on ADR 0055, skips fork pull requests without a red check, and says what the base-branch checkout protects.
tags:
- plan
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T12:49:55+00:00'
slug: adr-0057-pr-audit
epic: null
depends_on: []
priority: null
schema_version: '2.0'
---

# adr-0057-pr-audit

Relayed from: none

## Intent

Revise the draft ADR 0057,
`new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`,
on PR 71's branch `adr/audit-pull-requests`, so it answers the review of that
pull request. The work goes to PR 71: the ticket's commits are pushed to that
branch, not landed on main by `loopctl ticket land`.

The draft was written before ADR 0055
(`.okf/decisions/0055-one-verify-for-the-pages-a-branch-made-due.md`) added
`kmctl review due --base REF`, which already lists what a branch made due and
which `action/knowledge-ci.sh` shows on every pull request. The draft's Context
argues from the old 48-page list and never says why `--base` does not do the
scoping. Its own `sources` matcher stays: `--base` compares sources only for
verified decisions, and none is verified. Its fork rule "refuses" a fork pull request,
which in `action.yml` is `exit 1` and a red check. Its Decision reads as if
loading instructions from the base branch protects the API key, though on a
`pull_request` event GitHub runs the pull request's own workflow file.

It worked when the revised ADR passes the repo's hooks (`prek run --all-files`)
and every review point below is answered in its text, checked row by row in the
eval.

## Problems

- P1: The Context predates ADR 0055: it argues from the full `kmctl review due` list and never says why `kmctl review due --base` does not already do the scoping. That command compares `sources` only for a page with a `verified` entry; none of the 49 stable decisions has one, so over the last 15 merged pull requests it listed 0 of 82 decisions whose sources the pull request changed (spike:adr-0057-pr-audit/1). The record keeps its own `sources` matcher, but must say why, and what the audit adds on top of 0055 (whether a decision still holds, not only which pages a change touched).
- P2: The fork rule says the action refuses a fork pull request, which the "Check the event" step in `action.yml` does with `exit 1`, so a fork gets a red check while the record says a finding never fails the check and forks get the free checks only.
- P3: The Decision presents the base-branch checkout of prompt, system prompt, skills and context as a guard, but a same-repository author can edit the workflow on a `pull_request` event; what the checkout protects is the audit's honesty (a pull request cannot loosen the instructions that check it), not the key.
- P4: Smaller gaps: the new shipped audit is called "new" in one place and "fourth" in another and is never named next to `AUDITS` in `action/agent.py`; the record does not say the merge-base comparison relies on the audit's existing `fetch-depth: 0` requirement; and it says nothing about where the feature sits under ADR 0046's split between kmctl and kmaudit.

## Goals

- G1: The operator can accept ADR 0057 on an argument that matches main and on rules that agree with each other and with `action.yml`.

## Outcomes

### O1: The Context says why ADR 0055's `--base` list does not scope the audit
- kind: support
- goal: G1
- fixes: P1
- needs: none
- touches: `new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: eval rows that grep the record for a link to ADR 0055, for the reason `review due --base` misses unverified decisions with the measured 0 of 82, for the scoping rule still matching `sources` (files, and folders as prefixes), and for a sentence on what the audit adds over 0055
- seen by: operator

### O2: A fork pull request is skipped with a notice and exit 0
- kind: support
- goal: G1
- fixes: P2
- needs: none
- touches: `new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: an eval row that greps the fork rule for a skip that exits 0 and for no "refuses" wording
- seen by: operator

### O3: The record says the base-branch checkout protects the audit's honesty, not the key
- kind: support
- goal: G1
- fixes: P3
- needs: none
- touches: `new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: an eval row that greps the instructions rule for the honesty reason and for the note that the pull request's own workflow file runs
- seen by: operator

### O4: The audit is named, the history need is stated, and the package placement is settled
- kind: support
- goal: G1
- fixes: P4
- needs: none
- touches: `new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: eval rows that grep for the audit's name used the same way throughout, for `fetch-depth: 0`, and for a link to ADR 0046
- seen by: operator

### O5: PR 71 carries the revised ADR and it passes the repo's hooks
- kind: behaviour
- goal: G1
- fixes: P1
- needs: O1, O2, O3, O4
- touches: `new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`, `.okf/log.md`
- checked by: `prek run --all-files` green in the worktree, and `git log origin/adr/audit-pull-requests` showing the ticket's commit after the push
- seen by: operator

## Could invalidate this plan

- 1. Delivery to PR 71: loopctl builds a ticket in a worktree on `loop/adr-0057-pr-audit` cut from main, and `loopctl ticket land` merges into main. If the worktree cannot carry PR 71's branch (by merging `origin/adr/audit-pull-requests` into it, which is then a fast-forward push back), or `loopctl ticket done` cannot close the ticket without a land, the work cannot go to PR 71 through the loop and the plan changes. spike:adr-0057-pr-audit/2 settled it: main and PR 71's head merge with no conflict and the backstop lets the merge through; `ticket done` takes the newest `Loop-Ticket` commit on `loop/SLUG` and never calls land. Building merges `origin/adr/audit-pull-requests` with `--no-commit`, makes the edits, and commits it all as the one stamped `Loop-Ticket` merge commit, then pushes `loop/adr-0057-pr-audit` to `adr/audit-pull-requests` as a fast-forward. `ticket land` waits until PR 71 has merged, when it only cleans up.
