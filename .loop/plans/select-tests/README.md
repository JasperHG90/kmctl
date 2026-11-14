---
type: plan
title: 'Plan: select-tests'
description: The tests gate runs only the tests a change can reach, chosen from a per-test coverage map.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T12:20:00+00:00'
slug: select-tests
epic: null
depends_on: []
priority: 0
schema_version: '2.0'
---

# select-tests

Relayed from: none

## Intent

Every `loopctl gate stamp` runs the whole default suite: about 1400 tests in
17 minutes on the last stamp (the integration gate took 12 more). A ticket
stamps several times across building and review rounds, so most of a
ticket's wall time is spent on tests its change cannot reach. The operator
pointed at a selector already built for loopctl's own repository
(JasperHG90/loop-engineering-harness, `tests/tools/select_tests.py` and its
`covhook/`): a full run records which tests ran which lines, and later runs
pick only the tests whose covered lines, test files or fixtures changed,
falling back to a full recorded run when the map cannot answer.

This ticket ports it to this repository as
`new:tests/tools/select_tests.py` with its `covhook/` plugin, swaps its
fallback and narrowing rules for this repo's (the APM package under `apm/`
that the wheel force-includes and `kmctl briefing` reads, `tests/fixtures/`,
the conftest files, `pyproject.toml` and `uv.lock`). The operator wants it
first, before the kmaudit epic, so its rules name paths, not packages: when
kmaudit-package adds `packages/kmaudit/`, its source is covered like `src/`
and its conftest and fixtures fall back like the root ones. It points the
`tests` gate in `.loop/config.toml` at `select_tests.py run`. The integration gate stays a full run.

It worked when a stamp after a typical change runs a fraction of the suite
and still fails whenever the full suite would. The fraction is measured
first (risk 1); if it is small, the ticket is dropped with that number.

## Problems

- P1: Each stamp runs every default test, whatever the change touched, so a ticket waits about 17 minutes per stamp.

## Goals

- G1: A stamp runs the tests a change can reach and no fewer.

## Outcomes

### O1: The tests gate runs a selection from a coverage map
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:tests/tools/select_tests.py`, `new:tests/tools/covhook/sitecustomize.py`, `new:tests/tools/covhook/pytest_select_progress.py`, `new:tests/tools/__init__.py`, `.loop/config.toml`, `pyproject.toml`
- checked by: tests ported from the original's `test_select_tests.py` (selection by changed lines, test files, unknown tests, fallbacks), and a stamp after a one-function change runs fewer tests than the full suite
- seen by: operator

### O2: A change the map cannot answer runs everything
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `new:tests/tools/select_tests.py`
- checked by: tests that a change under `apm/`, `tests/fixtures/`, a conftest file, `pyproject.toml` or `uv.lock` records a full run
- seen by: nobody

## Could invalidate this plan

- The saving may be small: if most commits on this repository touch a
  fixture, a conftest, `pyproject.toml` or the `apm/` package, the selector
  falls back to a full run nearly every time. Measure it: record a map at an
  older commit, then for each later non-merge commit count the tests the
  selection would run against the full suite.
- Tests that run kmctl as a separate process from a built or installed copy
  (41 test files use subprocess; some build a wheel or install into a venv)
  cover site-packages paths, not `src/`, so the map may miss lines those
  tests reach and leave out tests a change breaks. Measure how many tests'
  coverage maps to no `src/` line although they drive kmctl.
