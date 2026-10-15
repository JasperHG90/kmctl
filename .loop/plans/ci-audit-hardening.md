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

- f3: `action.yml` sets `GH_TOKEN` for the whole audit step, so `claude` and its tools inherit it. The Read tool can read `/proc/self/environ`, and the model's text goes into the issue. The action passes the token under another name, and the script hands it to `gh` alone and removes it from the environment `claude` runs in.
- f4: without `pipefail`, a failed `gh issue list` gives an empty issue number, and the script opens a second "Knowledge audit" issue. The script checks the lookup's exit status and fails the step with a message, opening nothing.

Measured on main: the audit step's environment holds `GH_TOKEN` in 1 of 1 runs (action.yml sets it for the step), and the stub run in spike:ci-audit/4, where `gh issue list` printed nothing, went on to `issue create`.

Done when a test shows the stub `claude` sees no GitHub token in its environment while the stub `gh` does, and a test shows a failing `gh issue list` exits nonzero with no `issue create` or `issue edit` call.

## Could invalidate this plan

- none
