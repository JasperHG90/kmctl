---
type: eval
title: 'Eval: kmaudit-namespaces-nested-store'
description: 'Definition of done for kmaudit-namespaces-nested-store: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:04:56+00:00'
slug: kmaudit-namespaces-nested-store
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 67f09a84ee3c2b44e3d0c2ac2f6de8434431dae8a145770db8594b7259f406a5
  at: '2026-11-15T05:04:56+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit namespaces --json lists a nested namespace (handbook/guides, whose store file is handbook%2Fguides.sqlite) with its section count, and a top-level one beside it, without an error.
  Fails when: the command fails, leaves the nested namespace out, or reports its counts as 0 when its store holds a section
- r2: kmaudit briefing reports a nested namespace's audit state, read from its store.
  Fails when: briefing fails or leaves the nested namespace out
- r3: Read-only store URIs are built from the store's absolute path with Path.as_uri, so a repository path holding %, # or ? opens, including the legacy store copy, and a relative store path works too.
  Fails when: a store under a path with %, # or ? fails to open or copy, or a relative path raises
