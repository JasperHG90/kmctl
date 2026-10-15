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
- Every `kmctl plugin install` or `update` call in those tests asserts its expected exit code with the command output (`result.exit_code == 0, result.output` where it should succeed; the two calls meant to fail, in `test_installed_version_check_after_upgrade` and `test_install_reports_refused_entry`, keep their expected nonzero exit and add the output to the assert), so a failed install stops the test there with kmctl's message instead of failing later on a missing manifest or a status assert. Six tests ignore that result today (`test_staged_version_matches_cli`, `test_update_after_bump`, `test_status_reports_mismatch_and_missing_path`, `test_status_ignores_other_repositories`, `test_installed_version_check_after_upgrade`, and the first install in `test_install_declares_okf_in_each_repository`), so a network error never reaches the failure report (round 1 plan review). kmctl's `PluginError` keeps the last line of claude's stderr, which for a failed clone is git's line naming the host; a spike confirms it by making github.com unreachable.
- In that tier, a test that fails with a network error in claude's output (git's wording, as kmctl passes it on: `Could not resolve host`, `Failed to connect`, `Connection refused`, `Connection timed out`, `Operation timed out`, `Temporary failure in name resolution`) runs again up to two more times, a few seconds apart, from `tests/conftest.py` with no new dependency. Any other failure is reported at once, and three network failures still fail.

Measured in this session: 2 red stamps came from a network error in this file (init-claude-md-always's first full run, 6 failures; new-concept-freshness's first stamp, 1), both green on a rerun with nothing changed; and 0 of the file's network tests carry a marker today.

Done when the default `uv run pytest` collects none of the network tests and the `integration` gate runs all of them; an unregistered marker fails collection; a network-marked test failing twice with "Could not resolve host" then passing is reported as passed, one failing with another message is not rerun, and one failing three times with a network error is reported as failed; every test in `tests/test_plugin_install.py` that adds the okf marketplace from GitHub carries the marker; and every `kmctl plugin install` or `update` call in that file asserts its expected exit code with the output.

## Could invalidate this plan

- Settled by spike:network-tests-retry/1: with github.com unresolvable for git, kmctl's message and the pytest report of an asserted install both carry git's `Could not resolve host`; claude's own "Network error or timeout" line is dropped by `_require`, so the retry matches git's wording.
