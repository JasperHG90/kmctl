---
type: verdict
title: 'Verdict: ci-per-package plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of ci-per-package: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:49:14+00:00'
slug: ci-per-package
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: per-package pytest jobs from the root, an aggregate `tests` job with `if: always()` that keeps the required check, and a partition test against the gate's collection. Two facts are wrong. The just install and the starter job's path assume tests/test_starter.py stays at the root, but the ticket this depends on moves it into packages/kmctl/tests. And O1 is marked as a behaviour that can ship alone, when without O2 every merge stops. Both can be fixed by revising the plan; neither needs a rethink.

## Checked

- Read the plan, the signed eval rows, the epic brief and the kmctl-to-packages plan (its list of tests that stay at the root, its O-list touches, and its spike-2 note: 876 kmctl, 276 root and 255 kmaudit collected, with `-p pytester` in the root addopts).
- Read .github/workflows/ci.yml, tests/test_ci.py, tests/scripts/test_workflows.py (test_ci_and_release_test_jobs_install_just, test_ci_starter_job_bootstraps_a_generated_project), .loop/config.toml, the justfile and the root pytest config.
- Grepped the tests that need just: only tests/test_starter.py runs it (`JUST = shutil.which("just")`, asserted in a non-integration test). test_briefing.py only mentions it in strings. test_starter.py imports conftest and kmctl, so it moves.
- Checked that kmctl-to-packages never touches ci.yml.
- Confirmed the ruleset's required checks with `gh api repos/JasperHG90/kmctl/rulesets/25313903`: knowledge, prek, tests.
- spike:ci-toiminnot/2 backs the `markers: not integration` claim (an empty marker gives `-m ""` and runs the integration tier).
- packages/kmaudit/pyproject.toml has no pytest table. So `uv run pytest packages/<pkg>/tests` from the root still finds the root pyproject's config (addopts, pythonpath, `-p pytester`), as long as packages/kmctl/pyproject.toml also gets none, which kmctl-to-packages implies ("shared ruff and pytest config" at the root).

## Findings

- p1: the just install and the starter path follow a test file the dependency moves. The `kmctl` job needs just, and the `starter` job must run packages/kmctl/tests/test_starter.py. Eval row r1 should pin the `kmctl` job installing just before pytest, and the starter job's path.
- p2: O1 cannot ship without O2, because the required `tests` check would never report. Fold the aggregate job into O1, or keep O2 from being split away from it.

## Notes

- The Could-invalidate section says "none". One gap could be spiked but does not block: the O3 partition test checks file paths against the root collection, which shows coverage only if each per-directory run collects the same tests as the root run. With rootless conftests and `-p pytester` in the root addopts, that should hold. A cheap spike on the moved tree could confirm it: does `uv run pytest --collect-only -q packages/kmctl/tests` (and the same for kmaudit and tests) give 876/255/276, summing to the gate's 1407? Counting per job in the test itself would also close it.
- The how-to docs cite ci.yml by path and job (`knowledge`), which stays. The starter's own ci.yml (tests/test_starter.py:158) is a different file.
