---
type: plan
title: 'Plan: network-tests-retry'
description: "The plugin install tests that reach GitHub become an integration tier, left out of the default pytest run as the python-testing rule asks, run at every stamp by a gate of their own, and retried on a network error only."
slug: network-tests-retry
epic: repo
depends_on: []
priority: 7
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T17:49:28+00:00'
---

# network-tests-retry

Relayed from: init-claude-md-always's review (round 1 note: "a network failure can turn the gate red at random. It deserves its own ticket") and new-concept-freshness's build, where the first stamp went red on "Could not resolve host: github.com".

## Intent

`tests/test_plugin_install.py` runs the real `claude` CLI, which adds the okf marketplace by cloning from GitHub. They run in the default `uv run pytest`, which breaks the python-testing rule ("Tests that hit real external systems (network ...) must carry a marker ... and be excluded from the default run via `addopts`"), and when the network drops for a moment the tests gate goes red with nothing changed. The rule also says a tier left out of the default run must still run before merge (every-tier-runs-somewhere), so they cannot simply be dropped from the stamp.

- The tests in that file that reach the network carry an `integration` marker. `pyproject.toml` registers it under `markers` with a description saying where it runs, turns on `--strict-markers`, and leaves it out of the default run with `-m "not integration"` in `addopts`.
- `.loop/config.toml` gains a gate, `integration`, that runs `uv run pytest -m integration`, so every stamp still runs them. This is a gate added, not one weakened: the existing `tests` gate keeps running everything else.
- In that tier, a test that fails with a network error in claude's output (could not resolve host, connection refused or reset, timed out, temporary failure in name resolution) runs again up to two more times, a few seconds apart, from `tests/conftest.py` with no new dependency. Any other failure is reported at once, and three network failures still fail.

Measured in this session: 2 red stamps came from a network error in this file (init-claude-md-always's first full run, 6 failures; new-concept-freshness's first stamp, 1), both green on a rerun with nothing changed; and 0 of the file's network tests carry a marker today.

Done when the default `uv run pytest` collects none of the network tests and the `integration` gate runs all of them; an unregistered marker fails collection; a network-marked test failing twice with "Could not resolve host" then passing is reported as passed, one failing with another message is not rerun, and one failing three times with a network error is reported as failed; and every test in `tests/test_plugin_install.py` that adds the okf marketplace from GitHub carries the marker.

## Could invalidate this plan

- none
