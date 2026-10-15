---
type: verdict
title: 'Verdict: plugin-install-known-marketplace plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of plugin-install-known-marketplace: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:40:58+00:00'
slug: plugin-install-known-marketplace
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p4 is fixed: the plan now merges as claude does, and r2 checks the last of two
managed files, skipped dot-files, and managed over user. p1 to p3 stay resolved.
One new premise is wrong. Passing the entry's `url` as the add argument only
works when claude parses that string back into the same entry. For a git entry
whose URL does not end in `.git` it does not, and the add is refused with the
operator's error (p5). The fix is a revision, not a rethink: add those entries
to the "no matching add argument" case, and test it.

## Checked

- Plan text against round 2's p4: user first, then managed-settings.json, then
  sorted non-dot managed-settings.d/*.json, later replaces the whole entry. This
  matches `UDo` and `xw` in the 2.1.300 binary as read in round 2.
- Each row against the done-when list: r1 matches the add-argument and no-entry
  items, r2 the managed-precedence item, r3 the PluginError item (it also covers
  headers and headersHelper, which the intent names), r4 the real isolated
  install, r5 the existing tests. Every fails_when matches its item.
- Spike plugin-install-known-marketplace/1 covers one git URL ending in `.git`.
  It does not cover other git or url forms.
- Read claude's add-argument parser `Jme` and the check `bnt` in the 2.1.300
  binary (strings copy in the scratchpad, not the real ~/.claude).
- Probe in /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/review-mkt-plan-r3/probe:
  a user git entry without `.git` and an add from that exact URL exits 1 with
  "its source doesn't match its extraKnownMarketplaces entry". The settings file
  was left unchanged.

## Findings

- p1 resolved: github and git carry `#ref`.
- p2 resolved: extra fields and unknown kinds stop before claude runs.
- p3 resolved: the managed files and OS folders are named.
- p4 resolved: the last managed entry wins, and r2 tests it.
- p5 (open, premise): for a git entry without `.git` (and a self-hosted git URL,
  an ssh:// URL, or a url entry on a known git host), claude does not read the
  entry's own URL back as the same source. kmctl would pass an argument that
  claude refuses, and the tests in r1 and r3 would still pass. The plan should
  stop with the PluginError for these entries, and a row should cover one.

## Notes

The operator's own case (a `.git` URL) works under the plan as written. p5 is
about the contract "passes the argument claude accepts for it", which is wrong
for a class of entries an operator could easily write. The simplest rule is a
round trip: for git, accept a url that ends in `.git`, contains `/_git/`, or is
scp-style `user@host:path`; for url, accept one that is not one of those and not
on a known git host; otherwise stop.
