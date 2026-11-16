---
type: eval
title: 'Eval: adr-kmaudit-stale-lines'
description: 'Definition of done for adr-kmaudit-stale-lines: 1 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T06:44:34+00:00'
slug: adr-kmaudit-stale-lines
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 97ce8561c8e3a10809c6c469c9b5a00f9b4130164f58ec94c99891941a0723e7
  at: '2026-11-16T06:44:34+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: ADR 0012's last section is a dated correction that names packages/kmctl/apm/apm.yml and packages/kmaudit/apm/apm.yml as the two version sources, names every path in release-tag.yml's paths filter, and links ADR 0045; the earlier release-docs tests and kmctl check still pass.
  Fails when: the last section does not name both apm.yml files, misses a path release-tag.yml watches, does not link 0045, or any test in test_release_docs.py fails
