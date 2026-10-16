---
type: eval
title: 'Eval: apm-only-install-reviewer-f2'
description: 'Definition of done for apm-only-install-reviewer-f2: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-16T22:21:31+00:00'
slug: apm-only-install-reviewer-f2
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: fa4e5c7b61090d15581c6cd4cf569f4b3811f4f754c48b9048b307fe7cbc9ba6
  at: '2026-10-16T22:21:31+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: After an install from a local --source (http://127.0.0.1:PORT/o/kmctl.git), recorded in apm.lock.yaml in APM 0.33.0's shape (repo_url o/kmctl, host 127.0.0.1, port PORT, name kmctl, virtual_path apm), an install with the default source leaves exactly one kmctl entry in apm.yml, at the new source and in the old entry's place, and prints a note naming the replaced entry; the reverse order (default first, then the local source) gives the same result and runs no apm uninstall.
  Fails when: apm.yml holds two kmctl entries in either order, the entry is not at the new source, its position changed, no note names the old entry, the reverse order runs apm uninstall, or the lock fixture is not in APM's host/port/repo_url shape
- r2: An apm.yml entry with path: apm that the lock records under a name other than kmctl is kept unchanged.
  Fails when: that entry is removed or changed
- r3: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
