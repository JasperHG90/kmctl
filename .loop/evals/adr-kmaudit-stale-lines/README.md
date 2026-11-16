---
type: eval
title: 'Eval: adr-kmaudit-stale-lines'
description: 'Definition of done for adr-kmaudit-stale-lines: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T06:56:08+00:00'
slug: adr-kmaudit-stale-lines
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 25b6bc6fdfd420e27e85473db4eac1975eca1b34dc574760dbd204f3cbe861d7
  at: '2026-11-16T06:56:08+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: ADRs 0001, 0012 and 0014 each have a dated correction that names packages/kmctl/apm/apm.yml and links ADR 0045; ADR 0012's also names packages/kmaudit/apm/apm.yml and every path in release-tag.yml's paths filter.
  Fails when: any of the three lacks such a correction, ADR 0012's misses kmaudit's apm.yml or a path release-tag.yml watches, or the link to 0045 is missing
- r2: The decisions index notes for ADR 0012 and ADR 0014 name no path that ADR 0045 removed (a bare apm/apm.yml or the apm/ folder), and every earlier release-docs test, including kmctl check over the bundle, passes.
  Fails when: either index note still names apm/apm.yml or 'in apm/' outside packages/, or any test in test_release_docs.py fails
