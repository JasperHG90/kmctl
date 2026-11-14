---
type: eval
title: 'Eval: kmaudit-briefing'
description: 'Definition of done for kmaudit-briefing: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T14:05:40+00:00'
slug: kmaudit-briefing
signoff:
  signer: delegated:jasperginn@gmail.com/claude-main
  hash: b147be953b0359bf516cdfeae38cbf7892704e85dd681e134d3fa4ee34e629df
  at: '2026-11-14T14:05:40+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: `kmaudit briefing --json` reports, per namespace, sections, pending sections, claims, checks by status and open feedback; sections, claims, check statuses and open feedback match what `kmaudit claims list` and `kmaudit checks list` report for that namespace, and pending is the count of sections whose page is new or changed. Without --json it prints a few lines per namespace and one next step.
  Fails when: a namespace is missing, a matched count differs from the list commands, pending differs from the sections a fresh cut finds unextracted, or the text output names no next step while sections are pending
- r2: The briefing is read-only: with only an old .kmctl/audit.sqlite, or with stores under .kmaudit/, no store is created, copied or migrated (no .kmaudit/ appears where there was none) and every .sqlite file's bytes are unchanged; only SQLite's -wal and -shm sidecar files may appear. This holds even when a page changed since extraction, and the changed page's sections are counted pending.
  Fails when: a .kmaudit/ folder or a new .sqlite file appears, any .sqlite file's bytes change, or the changed section is not counted pending
- r3: A section whose stored key was made under a hash in PREVIOUS_HASHES reads as up to date in the briefing, as the store's refresh would treat it.
  Fails when: such a section is counted pending
- r4: In a repository with no namespace the briefing prints nothing and exits 0; with a store it cannot read it prints one line saying the briefing is unavailable and exits 0.
  Fails when: either case exits nonzero, the empty case prints anything, or the broken case prints a traceback or more than one line
