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

This ticket assumes `kmctl-to-packages` has landed. kmctl lives in
`packages/kmctl`, and its tests in `packages/kmctl/tests`, including
test_starter.py and conftest.py, which move there from the root tests/. kmaudit
stays in `packages/kmaudit`. The repo-level tests that plan keeps at the root
(`tests/scripts/`, `tests/test_agent.py`, `tests/test_audit.py`,
`tests/test_ci.py`, `tests/test_repo_apm.py`, `tests/test_rules.py`,
`tests/test_skills.py`, `tests/vendor/`) stay in `tests/`. If that ticket puts
a test file elsewhere, the job directories below follow it. Paths written
here as packages/kmctl/tests/test_starter.py are the moved files, which this
ticket does not create.

`.github/workflows/ci.yml` keeps its file name (docs and tests cite it) and
becomes `name: CI`. The jobs stay ordered so a cheap failure stops the run
early: `prek`, then `knowledge` (`uses: ./`), then side by side:

- `kmctl`: kmctl's tests, `packages/kmctl/tests`, with just installed first,
  because packages/kmctl/tests/test_starter.py runs the template's just
  recipes (and asserts just is on PATH in a default-tier test);
- `kmaudit`: kmaudit's tests, `packages/kmaudit/tests`;
- `repo`: the repo-level tests in `tests/`;
- `starter`: the bootstrap integration test, now
  `uv run pytest packages/kmctl/tests/test_starter.py -m integration`;
- `tests`: a job that collects the other three. It needs `kmctl`, `kmaudit`
  and `repo`, runs with `if: always()`, and fails unless all three succeeded.

Each test job uses the same pinned `JasperHG90/toiminnot/actions/pytest`
step as today, with `markers: not integration` (spike:ci-toiminnot/2: an
empty marker clears the filter) and its own `directory`. That action syncs at
the repo root and runs `uv run pytest DIRECTORY`, so the uv workspace, the
root dev group and the root pytest config (addopts, pythonpath,
`-p pytester`) apply to every job, as long as neither package's
`pyproject.toml` gets its own pytest table.

The `tests` job ships in the same outcome as the split, because without it
no pull request can merge. Main's ruleset (id 25313903, read with
`gh api repos/JasperHG90/kmctl/rulesets/25313903`) requires the status checks
`prek`, `knowledge` and `tests`. The operator chose this job over changing
the ruleset. `if: always()` matters: a job skipped because a job it needs
failed reports as passing to a required check. `prek`, `knowledge` and
`tests` keep their ids and get no `name:`, because the check takes the job's
name.

The loop's gates do not change. The `tests` gate in `.loop/config.toml` and
`just test` in `justfile` stay `uv run pytest` at the root, which collects
both packages and `tests/` (kmctl-to-packages measured 876 kmctl, 255
kmaudit and 276 root tests on the moved tree, 1407 together). A new test
collects each CI test job's directory on its own and checks that the counts
add up to the gate's root collection, with every test in exactly one job, so
CI and the gates cannot drift.

Outcome that shows it worked: on the pull request, the CI run shows separate
`kmctl`, `kmaudit` and `repo` jobs, each green, and the required `tests`
check reports from the collecting job.

Decisions already made for the epic (not reopened here): D1 layout
(`packages/kmctl`), D2 tag families, D3 notes in the version pull request, D5
the release skill. Only D4 is this ticket's. `.github/workflows/release.yml`
also runs the tests; it belongs to `release-per-package`.

## Problems

- P1: `.github/workflows/ci.yml` is named `ci` and runs every package's tests in one `tests` job at the root, so a red run does not say which package broke and one package cannot be rerun alone
- P2: once the tests are split, nothing checks that CI's test jobs and the loop's `uv run pytest` gate still run the same tests

## Goals

- G1: The CI workflow is named `CI` and reports kmctl, kmaudit and the repository's own tests as separate jobs, while main's required checks `prek`, `knowledge` and `tests` keep reporting
- G2: CI and the loop's gates run the same tests, both packages included

## Outcomes

### O1: ci.yml is named CI, runs one pytest job per package plus the repo tests, and a tests job keeps the required check
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `.github/workflows/ci.yml`, `tests/test_ci.py`, `tests/scripts/test_workflows.py`
- checked by: `tests/test_ci.py` pinning the name, the job order and needs (prek, knowledge, then kmctl, kmaudit, repo, starter, and tests after the three test jobs), each test job's pytest step and directory, and the `tests` job's needs, `if: always()`, its failure unless each result is success, and no `name:` on `prek`, `knowledge` or `tests`; `tests/scripts/test_workflows.py` checking the `kmctl` job installs just before pytest and the `starter` job runs packages/kmctl/tests/test_starter.py with `-m integration`
- seen by: operator

### O2: A test pins that the CI test jobs split what the gate collects, by count
- kind: support
- goal: G2
- fixes: P2
- needs: O1
- touches: `tests/test_ci.py`
- checked by: a test that runs `--collect-only` once per CI test job's directory and once with the `tests` gate's command from `.loop/config.toml` (and `just test` in `justfile`, both `uv run pytest`), then asserts each job collects at least one test, the per-job counts sum to the gate's count, the per-job test ids are disjoint and their union equals the gate's ids, and both `packages/kmctl` and `packages/kmaudit` appear
- seen by: nobody

## Could invalidate this plan

- none
