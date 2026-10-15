---
type: eval
title: 'Eval: ci-audit-hardening'
description: 'Definition of done for ci-audit-hardening: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T13:23:21+00:00'
slug: ci-audit-hardening
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 9aad6bb22b57199c7ce0bb67a5ff5eac1f68c15414c5bc3d0df96877d68a3b53
  at: '2026-10-15T13:23:21+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Only the issue step gets a GitHub token: action.yml's audit step env names no github.token, GH_TOKEN or GITHUB_TOKEN, and the issue step sets GH_TOKEN (f3).
  Fails when: the step running knowledge-audit.sh has GH_TOKEN, GITHUB_TOKEN or github.token in its env or run, or the step running knowledge-audit-issue.sh has no GH_TOKEN
- r2: The audit script makes no gh call and writes the issue body under $RUNNER_TEMP, and the summary still holds the findings.
  Fails when: with a stub claude that prints findings, the stub gh is called, or $RUNNER_TEMP holds no body with each finding's concept and verdict, or the summary lacks them
- r3: The audit script refuses to start when GH_TOKEN or GITHUB_TOKEN is in its environment, or git config holds a checkout extraheader, directly or through an included file.
  Fails when: in any of those four cases the script exits 0 or the stub claude is called
- r4: The shipped audit workflow sets persist-credentials: false and fetch-depth: 0 on checkout, and the mode help tells callers to set both.
  Fails when: .github/workflows/knowledge-audit.yml's checkout step lacks either, or action.yml's mode description does not name persist-credentials and fetch-depth
- r5: The issue script creates the issue, or edits the open one, from the body, and does nothing when no body was written.
  Fails when: with a body and no open issue gh issue create is not called; with an open Knowledge audit issue gh issue edit NUMBER is not called; with no body gh is called or the script exits nonzero
- r6: A failed issue lookup fails the issue step and opens no issue (f4).
  Fails when: with a stub gh whose issue list exits nonzero, the issue script exits 0, or gh is called with issue create or issue edit
- r7: The rest of the action's tests still pass.
  Fails when: any test in tests/test_ci_audit.py or tests/test_action.py fails
