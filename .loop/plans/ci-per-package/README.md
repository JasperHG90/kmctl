---
type: plan
title: 'Plan: ci-per-package'
description: Split the CI workflow into one test job per package, named CI, while main's required checks and the loop's gates keep covering both packages.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:21:46+00:00'
slug: ci-per-package
epic: monorepo-release
depends_on:
- kmctl-to-packages
priority: null
schema_version: '2.0'
---

# ci-per-package

Relayed from: none

## Intent

Decision D4 of the `monorepo-release` epic, routed under judgement
j-20261114T171913+0000-6d6b52c3. The operator: "tests.yml (should be called
CI)". The untracked `tests.yml` at the repo root gives the shape only: one
test job per package plus a job for the repository itself. Its registry,
cache and harness details do not apply, and it is never committed.

This ticket assumes `kmctl-to-packages` has landed: kmctl lives in
`packages/kmctl` with its tests, kmaudit stays in `packages/kmaudit`, and
repo-level tests (workflows, the action, the starter, the skills) stay in the
root `tests/`. If that ticket puts a test folder elsewhere, the job
directories below follow it.

`.github/workflows/ci.yml` keeps its file name (docs and tests cite it) and
becomes `name: CI`. The jobs stay ordered so a cheap failure stops the run
early: `prek`, then `knowledge` (`uses: ./`), then side by side:

- `kmctl`: kmctl's tests, `packages/kmctl/tests`;
- `kmaudit`: kmaudit's tests, `packages/kmaudit/tests`;
- `repo`: the repo-level tests in `tests/`, with just installed first,
  because `tests/test_starter.py` runs the template's just recipes;
- `starter`: unchanged, the bootstrap integration test;
- `tests`: an aggregate job that needs `kmctl`, `kmaudit` and `repo`, runs
  with `if: always()`, and fails unless all three succeeded.

Each test job uses the same pinned `JasperHG90/toiminnot/actions/pytest`
step as today, with `markers: not integration` (spike:ci-toiminnot/2: an
empty marker clears the filter) and its own `directory`. That action syncs at
the repo root and runs `uv run pytest DIRECTORY`, so the uv workspace and the
root dev group stay as they are.

Why the aggregate `tests` job: main's ruleset (id 25313903, read with
`gh api repos/JasperHG90/kmctl/rulesets/25313903`) requires the status checks
`prek`, `knowledge` and `tests`. Renaming the one `tests` job away would leave
every pull request waiting on a check that never reports. The aggregate keeps
that check meaning "every package's tests passed" with no settings change.
`if: always()` matters: a job skipped because a job it needs failed reports
as passing to a required check. `prek`, `knowledge` and `tests` keep their
ids and get no `name:`, because the check context is the job's name.

The loop's gates do not change. The `tests` gate in `.loop/config.toml` and
`just test` in `justfile` stay `uv run pytest` at the root, which collects
both packages and `tests/` (measured today: roots `packages/` and `tests/`
only). A new test pins that the three CI test jobs together run exactly what
that gate collects, each test in one job, so CI and the gates cannot drift.

Outcome that shows it worked: on the pull request, the CI run shows separate
`kmctl`, `kmaudit` and `repo` jobs, each green, and the required `tests`
check reports from the aggregate job.

Decisions already made for the epic (not reopened here): D1 layout
(`packages/kmctl`), D2 tag families, D3 notes in the version pull request, D5
the release skill. Only D4 is this ticket's. `.github/workflows/release.yml`
also runs the tests; it belongs to `release-per-package`.

## Problems

- P1: `.github/workflows/ci.yml` is named `ci` and runs every package's tests in one `tests` job at the root, so a red run does not say which package broke and one package cannot be rerun alone
- P2: main's ruleset requires a status check named `tests`, which only that one job reports, so splitting the job without a stand-in blocks every merge
- P3: once the tests are split, nothing checks that CI's test jobs and the loop's `uv run pytest` gate still run the same tests

## Goals

- G1: The CI workflow is named `CI` and reports kmctl, kmaudit and the repository's own tests as separate jobs
- G2: Pull requests stay mergeable under the existing ruleset with no settings change
- G3: CI and the loop's gates run the same tests, both packages included

## Outcomes

### O1: ci.yml is named CI and runs one pytest job per package plus the repo tests
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `.github/workflows/ci.yml`, `tests/test_ci.py`, `tests/scripts/test_workflows.py`
- checked by: `tests/test_ci.py` pinning the name, the job order and needs (prek, knowledge, then kmctl, kmaudit, repo, starter), and each test job's pytest step and directory; `tests/scripts/test_workflows.py` checking the `repo` job installs just before pytest
- seen by: operator

### O2: An aggregate tests job stands in for the required check
- kind: support
- goal: G2
- fixes: P2
- needs: O1
- touches: `.github/workflows/ci.yml`, `tests/test_ci.py`
- checked by: a test in `tests/test_ci.py` that the `tests` job needs `kmctl`, `kmaudit` and `repo`, runs `if: always()`, fails unless each result is success, and that `prek`, `knowledge` and `tests` carry no `name:`
- seen by: operator

### O3: A test pins that the CI test jobs partition what the gate collects
- kind: support
- goal: G3
- fixes: P3
- needs: O1
- touches: `tests/test_ci.py`
- checked by: a test that collects with the `tests` gate's command from `.loop/config.toml` (and `just test` in `justfile`, both `uv run pytest`), then asserts every collected test sits under exactly one CI test job's directory, every job directory collects at least one test, and both `packages/kmctl` and `packages/kmaudit` appear
- seen by: nobody

## Could invalidate this plan

- none
