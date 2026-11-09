---
type: plan
title: 'Plan: ci-audit-hardening'
description: "The audit mode keeps the GitHub token away from the model, and a failed issue lookup fails the step instead of opening a second issue (ci-audit review findings f3 and f4)."
slug: ci-audit-hardening
epic: ci
depends_on: [ci-audit]
priority: 12
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T13:18:22+00:00'
---

# ci-audit-hardening

Relayed from: ci-audit, reviewer findings f3 and f4 in review round 1 (stubs ci-audit-reviewer-f3 and ci-audit-reviewer-f4)

## Intent

Two gaps in `action/knowledge-audit.sh` and `action.yml`, both found by ci-audit's review:

- f3: `action.yml` sets `GH_TOKEN` for the whole audit step, so `claude` and its tools can read it. Removing it from `claude`'s own environment is not enough: `/proc/PID/environ` keeps the environment a process started with, so the step's shells still show the token to the Read tool (shown by the round 1 plan review). So the action splits the audit into two steps. The audit step runs `claude` with no GitHub token in its environment at all and writes the issue body to `$RUNNER_TEMP`. A later step, `new:action/knowledge-audit-issue.sh`, gets `GH_TOKEN`, runs no model, and does the issue lookup and the create or edit. `knowledge-audit.sh` no longer calls `gh`.
- `actions/checkout` keeps the token in the audited repository's git config by default (v4 as an `http.<url>.extraheader`; v6 in a file under `$RUNNER_TEMP` that `.git/config` includes), where Read can reach it too. The shipped `knowledge-audit.yml` sets `persist-credentials: false` and `fetch-depth: 0`, and the `mode` input's help says a caller's workflow must set both. The audit script refuses to start, before `claude`, when `git config --get-regexp '^http\..*\.extraheader$'` finds a header; `git config` reads included files, so that one check covers both checkout versions.
- f4: without `pipefail`, a failed `gh issue list` gives an empty issue number, and the script opens a second "Knowledge audit" issue. The issue script checks the lookup's exit status and fails the step with a message, opening nothing.

- A caller's workflow can still set `GH_TOKEN` or `GITHUB_TOKEN` at the job level, which the action cannot unset for one step. The audit script refuses to start when either is in its environment, and the `mode` help says why.
- The issue step runs only when the audit step wrote a body, so the nothing-due and no-findings paths open no issue.

`ANTHROPIC_API_KEY` stays readable in the audit step: `claude` needs it, and it is the key the model is already using, so it gives the model nothing new.

Measured on main: the audit step's environment holds `GH_TOKEN` in 1 of 1 runs (action.yml sets it for the step), the shipped audit workflow keeps checkout's default `persist-credentials: true`, and the stub run in spike:ci-audit/4, where `gh issue list` printed nothing, went on to `issue create`.

Done when a test shows the audit step in `action.yml` has no GitHub token in its `env`, the audit script makes no `gh` call and writes the body under `$RUNNER_TEMP`, only the issue step gets `GH_TOKEN`, the audit script exits nonzero before `claude` when `GH_TOKEN` or `GITHUB_TOKEN` is set or git config holds an extraheader, the issue script does nothing when no body was written, and the shipped workflow sets `persist-credentials: false`; and a test shows a failing `gh issue list` makes the issue script exit nonzero with no `issue create` or `issue edit` call.

## Could invalidate this plan

- none
