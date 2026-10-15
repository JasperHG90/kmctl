---
type: verdict
title: 'Verdict: ci-audit-hardening reviewer round 2'
description: 'reviewer verdict for round 2 of ci-audit-hardening: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:32:42+00:00'
slug: ci-audit-hardening
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed. The "Post the audit issue" step now sets `working-directory: ${{ inputs.path }}` and `GH_REPO: ${{ github.repository }}`, so gh finds the right repository for a nested checkout, and test_token_only_on_issue_step asserts both. The fix adds nothing to the audit step and breaks nothing else.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, eval rows r1 to r7 pass. "stamp green: 8f6df42ad781a3272518f3984b1ca53ab68567bff501a201682b22ea1a6a2c1b".
- action.yml lines 40 to 68: the audit step's env still holds only ANTHROPIC_API_KEY and KMCTL_PLUGIN_DIR. GH_TOKEN and GH_REPO sit in the issue step's own `env:`, which is step-scoped, so neither reaches the audit step's process. GH_REPO is not a credential either way.
- test_token_only_on_issue_step (tests/test_ci_audit.py:276): it still checks the audit step's dumped YAML for GH_TOKEN, GITHUB_TOKEN and github.token, and now asserts GH_REPO equals `${{ github.repository }}` and the issue step's working-directory equals the audit step's. Dropping either line from action.yml fails the test.
- action/knowledge-audit-issue.sh is unchanged and its gh calls (list, edit, create) all honour GH_REPO; the header still holds.

## Findings

- f1 (resolved): action.yml's issue step now has `working-directory: ${{ inputs.path }}` and `GH_REPO: ${{ github.repository }}`, asserted in test_token_only_on_issue_step.
