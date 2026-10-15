---
type: plan
title: 'Plan: network-tests-retry'
description: "The plugin install tests that clone from GitHub retry a network failure instead of turning the gate red, and still fail on any other error, so a DNS blip no longer stops a stamp."
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

`tests/test_plugin_install.py` runs the real `claude` CLI, which adds the okf marketplace by cloning from GitHub. When the network drops for a moment, those tests fail and the tests gate goes red, though nothing in the code changed. Keeping them out of the gate would weaken it; the tests cover the one path real users hit, so they stay in.

- The tests that reach the network carry a `network` pytest marker.
- A network-marked test that fails with a network error in claude's output (could not resolve host, connection refused or reset, timed out, temporary failure in name resolution) is run again, up to two more times, a few seconds apart. Any other failure is reported at once, as now. This lives in `tests/conftest.py`, with no new dependency, or with `pytest-rerunfailures` added as a dev dependency with its `--only-rerun` patterns if that is simpler.
- Without network at all, the tests still fail after their retries, so a gate never passes without having run them.

Measured in this session: 2 of the stamps that went red did so on a network error in this file (init-claude-md-always's first full run, 6 failures; new-concept-freshness's first stamp, 1), and both went green on a rerun with nothing changed.

Done when a test shows a network-marked test whose first two runs fail with "Could not resolve host" passes on the third and is reported as passed; one that fails with any other message is not rerun; one that fails with a network error three times is reported as failed; and every test in `tests/test_plugin_install.py` that runs `claude plugin marketplace add` from GitHub carries the marker.

## Could invalidate this plan

- none
