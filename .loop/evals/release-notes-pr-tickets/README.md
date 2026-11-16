---
type: eval
title: 'Eval: release-notes-pr-tickets'
description: 'Definition of done for release-notes-pr-tickets: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T06:43:40+00:00'
slug: release-notes-pr-tickets
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 6ffacc460087f676a57ed1beab7d495b9659be01470ad1853e33a75217499f64
  at: '2026-11-16T06:43:40+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: A pull request merge whose branch brought ticket merges into main drafts one What changed bullet per ticket (its summary and slug), in merge order, and no bullet for the pull request; plain commits on that branch's first-parent line go under Other changes; loop: commits and syncs on it stay out.
  Fails when: the pull request's title shows as a bullet, a ticket on its branch is missing or listed twice, a plain commit on its branch is missing from Other changes, or a loop: commit shows
- r2: A pull request with no ticket merges keeps its one title bullet; release pull requests stay out; with --package kmaudit only the tickets inside the pull request that touch packages/kmaudit/ are listed; every earlier release_notes test passes.
  Fails when: a plain pull request loses its bullet or gets its commits listed instead, a release pull request shows, a kmctl-only ticket inside the pull request is in kmaudit's notes, or any release_notes test fails
