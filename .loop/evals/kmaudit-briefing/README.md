---
type: eval
title: 'Eval: kmaudit-briefing'
description: 'Definition of done for kmaudit-briefing: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T14:00:41+00:00'
slug: kmaudit-briefing
signoff:
  signer: delegated:jasperginn@gmail.com/claude-main
  hash: 5f13809538c6767dc688c3ac18ec501a7d87006f158f4b068a45d061374472a5
  at: '2026-11-14T14:00:41+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: `kmaudit briefing --json` reports, per namespace, sections, pending sections, claims, checks by status and open feedback, matching what `kmaudit claims list` and `kmaudit checks list` report for that namespace; without --json it prints a few lines per namespace and one next step.
  Fails when: a namespace is missing, any count differs from claims list or checks list, or the text output names no next step while sections are pending
- r2: The briefing is read-only: every store file's bytes are equal before and after it runs, even when a page changed since extraction, and the changed page's sections are counted pending.
  Fails when: any store file changes, a changed section's claims are dropped, or the changed section is not counted pending
- r3: A section whose stored key was made under a hash in PREVIOUS_HASHES reads as up to date in the briefing, as the store's refresh would treat it.
  Fails when: such a section is counted pending
- r4: In a repository with no namespace the briefing prints nothing and exits 0; with a store it cannot read it prints one line saying the briefing is unavailable and exits 0.
  Fails when: either case exits nonzero, the empty case prints anything, or the broken case prints a traceback or more than one line
