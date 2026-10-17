---
type: verdict
title: 'Verdict: repo-ci plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of repo-ci: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T17:39:19+00:00'
slug: repo-ci
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: both listed risks are settled by spikes whose evidence answers them, and the repo's own tests keep passing with ci.yml in place of knowledge.yml. One scope gap must be fixed before building: the how-to doc quotes knowledge.yml as the shipped workflow, and the plan deletes that file without touching the doc (p1). Verdict fail, not reject; the plan needs one more item in scope, not a rethink.

## Checked

- Spike repo-ci/1: runner.sh does a fresh `git clone`, empty HOME, `GIT_CONFIG_GLOBAL=/dev/null`, PATH with only uv/git/system tools; `uv run pytest` gave 696 passed, 8 deselected, exit 0. That answers the bare-runner risk for the tests job.
- Spike repo-ci/2: same harness, `uvx prek@0.5.5 run --all-files` ran both local hooks, both passed, `git status --short` was empty. That answers the prek risk.
- The spikes used a full clone, while actions/checkout defaults to depth 1 for the prek and tests jobs. I checked whether that matters: `kmctl check` (src/kmctl/checks.py) does not call git; only review_due, plugin and doctor do, and review due runs in the knowledge job, which keeps fetch-depth 0. Tests that touch ROOT with git use `git ls-files`, which works on a shallow clone. Not a risk.
- tests/test_action.py:172 asserts some workflow contains `uses: ./`; ci.yml's knowledge job keeps that. tests/test_rules.py lists `.github/workflows/` as planned; fine. tests/test_audit.py reads only knowledge-audit.yml, which stays.
- action.yml in checks mode installs kmctl from the action checkout and runs action/knowledge-ci.sh, so `uses: ./` in ci.yml behaves as in knowledge.yml.
- justfile pins prek@0.5.5, matching the plan. pyproject addopts exclude the integration marker, so bare `uv run pytest` is the default tier as the plan says.
- release-tag.yml shows the SHA-pin style the plan copies.
- grep for knowledge.yml outside .loop/: only docs/how-to/install-the-plugin-and-the-ci-action.md references it (p1).

## Findings

- p1: the how-to doc claims its workflow is quoted from the shipped knowledge.yml, which the plan deletes; the plan's scope must include updating that doc (and r6's "knowledge.yml is gone" is the row that creates the gap).

## Notes

One ticket is the right size; no split needed.
