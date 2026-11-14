---
type: verdict
title: 'Verdict: ci-per-package plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of ci-per-package: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:52:06+00:00'
slug: ci-per-package
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are closed, and the round 1 note is taken up: O2's partition test now counts per job, checks the ids are disjoint and that their union equals the gate's collection, so it no longer rests on the guess that a per-directory run collects what the root run does. Nothing new could break the plan.

## Checked

- The plan, eval rows r1 to r3, and my round 1 verdict.
- .github/workflows/ci.yml today: the `tests` job installs just and runs the toiminnot pytest action at `.`; the `starter` job runs `uv run pytest tests/test_starter.py -m integration`. The plan's revisions cover both.
- tests/scripts/test_workflows.py: test_ci_and_release_test_jobs_install_just and test_ci_starter_job_bootstraps_a_generated_project, which O1 names and r1's `-k 'per_package or install_just or starter_job'` selects. Test names are left to the build.
- .loop/config.toml (`tests` gate is `uv run pytest`), justfile (`test: uv run pytest`) and the root `[tool.pytest.ini_options]` (addopts `-m "not integration"`). The gate and the CI jobs both apply the same marker filter, so a collect-only partition of selected ids compares like with like.
- kmctl-to-packages: test_starter.py and conftest.py move to packages/kmctl/tests; the root keeps exactly the list this plan names; spike 2/4 measured 876/276/255 = 1407 selected with `-p pytester` in the root addopts.
- spike:ci-toiminnot/2 still backs `markers: not integration`.
- Facts: P1 and P2 are separate causes; O1 (behaviour) ships alone with the aggregate job; O2 (support) cannot and needs O1; touches match the prose (ci.yml, test_ci.py, test_workflows.py; O2 only test_ci.py).

## Findings

- p1: resolved. The kmctl job installs just before pytest and the starter job runs packages/kmctl/tests/test_starter.py; r1 pins both.
- p2: resolved. The aggregate tests job is part of O1; r2 pins it.

## Notes

- kmctl-to-packages does not touch ci.yml, so between that ticket landing and this one, ci.yml's starter job still names tests/test_starter.py and fails. That is the dependency's gap, not this plan's; this plan fixes it.
- The partition test runs four collect-only subprocesses inside the gate. The CI repo job syncs the whole workspace at the root, so both packages import there. Cost is a few seconds per collection.
