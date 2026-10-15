---
type: verdict
title: 'Verdict: ci-audit-hardening plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of ci-audit-hardening: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:24:16+00:00'
slug: ci-audit-hardening
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

The plan can be built as written. The audit script now refuses to start when git config holds a checkout extraheader, and a scratch repository shows one `git config --get-regexp` call finds the header whether it sits in .git/config or in a file pulled in by `include.path` or `includeIf "gitdir:..."`. That covers checkout v4 and v6, so p3 is resolved. The eval rows now map one-to-one to the done-when items, so p4 is resolved. No open risk could break the plan.

## Checked

- The plan, the round 2 verdict, rows.json, action.yml, action/knowledge-audit.sh and .github/workflows/knowledge-audit.yml on main.
- git 2.51.1, scratch repository: with no header, `git config --get-regexp '^http\..*\.extraheader$'` exits 1. With the header set directly (checkout v4), through `include.path`, or through `includeIf.gitdir:<repo>/.git.path` pointing at a file outside the repository (checkout v6 writes one like this under RUNNER_TEMP), it exits 0 and prints the key. The included case also works from a subdirectory. So the one check covers both checkout versions.
- Rows against done-when: no token in the audit step env and GH_TOKEN only on the issue step (r1); no gh call and a body under RUNNER_TEMP (r2); refusal on GH_TOKEN, GITHUB_TOKEN, a direct header and an included header, before claude (r3); persist-credentials: false and fetch-depth: 0 (r4); the issue script does nothing with no body, and creates or edits with one (r5); a failing lookup exits nonzero with no create or edit (r6); no regressions (r7). Each fails_when tests its item. r5's create and edit cases go beyond done-when and keep today's behaviour under test.
- No spike folder exists for this ticket and the risk list says none. Nothing left needs a spike.

## Findings

- p1 resolved in round 2.
- p2 resolved in round 2.
- p3 resolved: the script refuses on an extraheader found by git config, which reads included files (checked above). The shipped workflow and the mode help name persist-credentials: false and fetch-depth: 0.
- p4 resolved: the rows are rewritten for the two scripts and each one matches a done-when item.

## Notes

- Send the check's output to /dev/null. `--get-regexp` prints the header value, so the token would go to the step log. GitHub masks it, but the script should not print it at all.
- If the issue step's `if:` checks for the body file, do not use `hashFiles`: it only looks under GITHUB_WORKSPACE, not RUNNER_TEMP. A step output, or the issue script's own no-body exit, works. r5 already tests the second.
- As round 2 noted, the test harness must remove GH_TOKEN and GITHUB_TOKEN from the env it passes to the audit script. It must also run in a repository whose git config has no extraheader, or the r2 and r7 tests fail in CI.
- Submodule configs are not covered by the check. The shipped workflow uses no submodules, so this does not affect the plan.
