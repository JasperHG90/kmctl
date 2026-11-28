---
type: decision
title: "ADR 0061: The reread runs on demand on a ready pull request"
description: "The pull request reread runs only when someone starts it with workflow_dispatch on a ready pull request's branch, so its check can be required and a refusal fails it."
tags: [decision]
generated:
  by: process:kmctl/0.18.0
  at: 2026-11-27T19:40:06Z
status: stable
sources:
  - resource: "action.yml"
  - resource: "action/agent.py"
  - resource: ".github/workflows/knowledge-audit.yml"
verified:
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0061: The reread runs on demand on a ready pull request

## Context

[ADR 0060](0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md)
ran the pull request reread on every `pull_request` push, drafts included.
Each push reread the same pages; over the 6 runs on pull request #83, 5
findings landed on pages the run before had passed. The operator wants the
check mandatory but started by hand, once a pull request is ready.

A required check reads the check runs on the pull request's head commit. A
`workflow_dispatch` started with `--ref` on a branch runs at that branch's
head and leaves its check there (spike:audit-keeps-state/3). GitHub counts a
skipped job as passing a required check.

## Decision

The reread runs on `workflow_dispatch` only, with a required `pr` input,
started on the pull request's branch:
`gh workflow run knowledge-audit.yml --ref BRANCH -f pr=NUMBER`.

- **Resolve first.** The previous job, which holds a read token, looks the
  pull request up with `agent.py previous --resolve SHA` and refuses one
  that is closed, a draft, from a fork, or whose head is not the run's
  commit. It passes the number, base branch and head on as outputs.
- **A refusal fails the check.** The audit job runs on `!cancelled()` and
  its first step fails unless the previous job succeeded, so a refused or
  wrong-branch dispatch leaves a failed `audit` check, never a skipped one.
  The starter's workflow fails, rather than skips, without `AUDIT_API_KEY`.
- **Mandatory.** The repository marks `audit` a required check. A push after
  a run leaves the new commit without the check, so the pull request waits
  for another run. Findings still never fail it
  ([ADR 0005](0005-audits-report-only.md)).
- **The action keeps both triggers.** It takes `pr`, `base` and `head`
  inputs for a dispatch, and reads them from the event on a `pull_request`,
  so a repository that keeps the old trigger is unaffected.

Rejected:

- **`pull_request` with a job-level `if` on drafts.** A skipped job passes a
  required check, so a draft would merge unaudited once marked ready.
- **Run on `ready_for_review` only.** Pushes after that run would leave the
  check stale with nothing to rerun it but a manual trigger anyway.
- **Dispatch on the default branch with a pull request number.** The check
  would land on the default branch's head, not the pull request's.

## Consequences

- An author starts the audit once the pull request is ready, and again
  after any later push, before it can merge.
- A fork's pull request cannot be dispatched, so a required `audit` check
  blocks it; a repository that takes fork contributions should not require
  it.
- This repository's workflow, the starter's and the how-to run on dispatch.

## Correction, 2026-11-28

A required check cannot read the dispatched run's `audit` check run: GitHub
counts only check runs from runs tied to the pull request, so requiring
`audit` blocked pull request #83 though its check had passed. The required
check reads a commit status named `audit` instead, which a dispatch run's
token can post and a ruleset entry for the GitHub Actions app accepts. A
`pull_request` workflow, `knowledge-audit-pending.yml`, marks it pending on
each push, with a Details link to the workflow's Run workflow button, and
the publish job sets it to success when the audit ran, failure when it did
not. A refused dispatch leaves it pending.

## Correction, 2026-11-28, after a push

The Decision says a push after a run leaves the new commit without the
check. With the `audit` commit status, the pending workflow marks the new
head pending on each push, with its Details link to run the audit, so the
pull request waits for another run with a pending check, not a missing one.
