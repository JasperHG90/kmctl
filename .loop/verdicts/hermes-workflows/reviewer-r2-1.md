---
type: verdict
title: 'Verdict: hermes-workflows reviewer round 2'
description: 'reviewer verdict for round 2 of hermes-workflows: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-20T09:03:52+00:00'
slug: hermes-workflows
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Narrow round. f1 is fixed: ADR 0035 now states what really happens when a member types `/hermes` in a fork's pull request conversation, and the new text matches the workflow. The fix touched nothing else. f2 stays open as non-blocking hardening, deferred to its own ticket, so the change can be committed.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r6 pass; stamp green 91afacb820bdfd5291de66aba49290365e6fbdbf9ca470f659632d9d19de86a5, the fingerprint this round binds to.
- Read ADR 0035 lines 55 to 80 against `.github/workflows/hermes-interactive.yaml`. The job condition skips only `pull_request_review_comment` events from a fork, so an `issue_comment` on a fork PR from a MEMBER, OWNER or COLLABORATOR runs with `OLLAMA_API_KEY` and checks out `refs/pull/N/head`. The ADR now says exactly this, names the member gate as the only guard, and says the inline review comments on a fork PR are skipped because they get no secrets. All three claims match the workflow.
- Grepped the ADR and `.okf/architecture/overview.md` for other mentions of forks; no other claim contradicts the new bullet.

## Findings

- f1 (resolved): the Consequences bullet at ADR 0035 lines 71 to 76 replaces the false "Neither job runs on a fork's pull request with the key" with an accurate account of the fork PR conversation path and its single guard.
- f2 (open, non-blocking hardening): not part of this round; the operator deferred it to stub ticket hermes-workflows-reviewer-f2. It does not block the commit.
