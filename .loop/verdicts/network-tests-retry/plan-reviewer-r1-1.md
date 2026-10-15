---
type: verdict
title: 'Verdict: network-tests-retry plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of network-tests-retry: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T19:08:57+00:00'
slug: network-tests-retry
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan is sound in shape: the marker, strict markers, the `addopts` exclusion and a separate `integration` gate all work as described, and r4's command runs both tiers. One premise does not hold: the conftest retry is meant to spot a network error in claude's output, but for six of the eleven network tests that output never reaches the failure report, so those tests would not be retried. Fail, to fix in the plan and look at again.

## Checked

- tests/test_plugin_install.py: eleven `needs_claude` tests run `kmctl plugin install` against the real claude CLI, and each adds the okf marketplace (`install` always runs `marketplace add okf` first, src/kmctl/plugin.py:254). test_wheel_carries_plugin only runs `uv build`. The okf_source and unknown-kind tests only stage settings files or mock `_claude`, so they need no marker.
- CI: .github/workflows/knowledge.yml and knowledge-audit.yml never run pytest or `just test`, so leaving a tier out of the default run hides it from no CI job. The stamp is the only place the tests run, and the new gate covers that (every-tier-runs-somewhere holds).
- tests/test_action.py and tests/test_ci_audit.py: they use local fixture repos, a `file://` clone, and stub hermes/gh with a base URL of 127.0.0.1:9. No real network, so no marker is needed.
- r4: `loopctl schema config` says a gate command is a shell command, so the double quotes are fine. I ran it in a scratch project with `addopts = ["--strict-markers", "-m", "not integration"]`: plain `pytest` gave 1 passed and 1 deselected, `-m "not integration or integration"` gave 2 passed (the command-line `-m` replaces the one in addopts), and `-m integration` gave the marked test only. The command works as written. `-m ""` or `uv run pytest -q && uv run pytest -q -m integration` would also work.
- How a failure reaches pytest: `_kmctl` uses CliRunner, `_require` keeps only the last line of claude's stderr, and `_listed()` uses `check=True`, which raises CalledProcessError without stderr.

## Findings

- p1 (premise, blocking): the network-error test is meant to read claude's output, but several tests never surface that output, so a DNS blip in them fails at once. The plan should name how the error reaches the hook (assert the install result in every network test, or capture claude's stderr), and r2's test should cover a test whose failure comes after an install that did not succeed.

## Notes

- test_wheel_carries_plugin runs `uv build`, which may fetch the build backend from PyPI on a cold cache. It does not add the okf marketplace, so the plan's rule leaves it unmarked. That is fine on this machine, but worth one line in the plan.
- Every network test is skipped when claude is not on PATH, so the integration gate passes with nothing run on such a machine. This was true before the ticket, and it does not break the plan.
