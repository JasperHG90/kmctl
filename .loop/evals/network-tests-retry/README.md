---
type: eval
title: 'Eval: network-tests-retry'
description: 'Definition of done for network-tests-retry: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T17:49:30+00:00'
slug: network-tests-retry
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 14950489e7640d16cf04e2de0f4440b0cef2b6a31f76d0872bea8a24c3863724
  at: '2026-10-15T17:49:30+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: A network-marked test that fails with a network error is run again up to two more times and reported as passed if a later run passes.
  Fails when: a network-marked test whose first two runs fail with 'Could not resolve host' and third passes is reported as failed, or runs more than three times
- r2: A failure that is not a network error is reported at once, and three network failures are reported as a failure.
  Fails when: a network-marked test failing with another message is rerun, or one failing with a network error three times is reported as passed or skipped
- r3: Every test in tests/test_plugin_install.py that adds the okf marketplace from GitHub carries the network marker.
  Fails when: such a test lacks the marker
- r4: The other tests still pass.
  Fails when: any test fails
