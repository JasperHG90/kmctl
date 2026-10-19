---
type: eval
title: 'Eval: commit-apm-installs'
description: 'Definition of done for commit-apm-installs: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.1.dev16+g27435b040.d20261017
  at: '2026-10-19T08:04:23+00:00'
slug: commit-apm-installs
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 5b89febedcc3f302f3310834ddd40935167b29bff2c6afe140e2bcc7f7c0938c
  at: '2026-10-19T08:04:23+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: A decision records that projects commit the files APM deploys and gitignore only apm_modules/, names PR #16 as the rejected alternative, and .okf/decisions/index.md links it.
  Fails when: the decision file is missing, it does not mention apm_modules or PR #16, or the index does not link it
- r2: kmctl check passes on the repository with the new decision.
  Fails when: kmctl check exits nonzero
