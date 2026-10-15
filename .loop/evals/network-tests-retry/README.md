---
type: eval
title: 'Eval: network-tests-retry'
description: 'Definition of done for network-tests-retry: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T19:10:50+00:00'
slug: network-tests-retry
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 54d564718295a3b6b6cb53faf5c1faa87b3632dbd392ebc4d33c99fdbbf16e45
  at: '2026-10-15T19:10:50+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The network tests are an integration tier: registered, strict markers on, left out of the default pytest run, and run by an integration gate in .loop/config.toml.
  Fails when: the default uv run pytest collects a test that adds the okf marketplace from GitHub, the marker is not registered or --strict-markers is off, or .loop/config.toml has no gate running uv run pytest -m integration
- r2: In the integration tier a network error is retried up to two more times; any other failure is reported at once; three network failures still fail.
  Fails when: a test failing twice with 'Could not resolve host' then passing is reported as failed or runs more than three times, a test failing with another message is rerun, or one failing three times with a network error is reported as passed or skipped; or a test whose install fails with a network error is not retried because the failure surfaces later as another error
- r3: Every test in tests/test_plugin_install.py that adds the okf marketplace from GitHub carries the integration marker.
  Fails when: such a test lacks the marker
- r5: Every kmctl plugin install or update call in tests/test_plugin_install.py asserts its exit code with the command output.
  Fails when: any such call's result is not checked with exit_code == 0 and its output
- r4: The default suite and the integration tier both pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
