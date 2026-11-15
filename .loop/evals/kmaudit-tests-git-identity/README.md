---
type: eval
title: 'Eval: kmaudit-tests-git-identity'
description: 'Definition of done for kmaudit-tests-git-identity: 1 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T20:55:39+00:00'
slug: kmaudit-tests-git-identity
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 646d87391b2ab5315ebd7f5e49cafaeb21c6e045157fcb1eef814fdf0476a3ad
  at: '2026-11-15T20:55:39+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit's tests pass on a machine with no global or system git config, as on a fresh CI runner, because the fixture's git helper commits with its own identity.
  Fails when: any kmaudit test fails or errors with GIT_CONFIG_GLOBAL=/dev/null and GIT_CONFIG_NOSYSTEM=1
