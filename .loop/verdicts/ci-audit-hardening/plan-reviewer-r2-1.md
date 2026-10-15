---
type: verdict
title: 'Verdict: ci-audit-hardening plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of ci-audit-hardening: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:22:13+00:00'
slug: ci-audit-hardening
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The split into an audit step with no GitHub token and an issue step with no model fixes p1. Setting persist-credentials: false in the shipped workflow fixes p2. The approach holds. Two things still need to change before building. A caller's default checkout still leaks the token through git config, and the plan only documents that (p3). The eval rows describe the round 1 design and must be rewritten (p4). Both are revisions, not a rethink, so the verdict is fail.

## Checked

- The revised plan, the round 1 verdict, rows.json, action.yml, action/knowledge-audit.sh, .github/workflows/knowledge-audit.yml and tests/test_ci_audit.py on main.
- GITHUB_TOKEN in a composite step's env: the runner does not put GITHUB_TOKEN or GH_TOKEN in any step's environment by default. github.token is only an expression value, and it reaches a process only when a step's env or with names it. Today's leak comes from action.yml's explicit `GH_TOKEN: ${{ github.token }}`. ACTIONS_RUNTIME_TOKEN is given to JavaScript and container actions, not to `run:` steps. That is why actions such as crazy-max/ghaction-github-runtime exist to expose it. ACTIONS_ID_TOKEN_REQUEST_TOKEN appears only with id-token: write, which the shipped workflow does not grant. So the claim that an audit step without an env entry holds no GitHub token stands, provided the caller adds no job-level env. The plan's refusal covers that case.
- RUNNER_TEMP between composite steps: it is one directory per job, shared by every step of the job, including the steps of a composite action, and emptied when the job ends. Writing the body there in one step and reading it in the next works. The current script's `mktemp -d` plus `trap rm` must not hold the body, or the body is gone before the issue step runs.
- The issue step runs after `claude` has exited. Read, Grep, Glob and Agent cannot start a process that outlives the step, so nothing model-driven is alive when GH_TOKEN appears.
- No spike folder exists for this ticket. The risk list says 'none'. Nothing in it needs running code to settle, beyond p3's check, which a unit test covers.

## Findings

- p1 resolved: the claude step no longer has the token in any ancestor's environment, because no step env sets it.
- p2 resolved for the shipped workflow: persist-credentials: false.
- p3: callers using checkout's default persist-credentials still expose the token in git config. The plan refuses the job-level env case in code but only documents this one. Detect checkout's credentials in git config and refuse, as with GH_TOKEN, or say in the plan why documentation is enough.
- p4: the eval rows match the round 1 single-script design and must be rewritten for the two scripts and the done-when list.

## Notes

- With persist-credentials: false, the audit script's `git fetch --unshallow` has no credentials. For a private repository with a shallow checkout it fails, and the script carries on with a note, so review due may see too little history. The shipped workflow uses fetch-depth: 0, so it is not shallow. The mode help should tell callers to set fetch-depth: 0 as well.
- The test harness passes os.environ through to the script. Once the script refuses on GH_TOKEN or GITHUB_TOKEN, a developer or CI shell that exports either (a Codespace does) makes every audit test fail. Remove both from the env in `_audit`.
- The issue step has to skip when no body was written: the nothing-due path and the no-findings path. Use a missing body file or a step output for that. This is a build detail.
- The ticket is still one coherent change, so it does not need to be split.
