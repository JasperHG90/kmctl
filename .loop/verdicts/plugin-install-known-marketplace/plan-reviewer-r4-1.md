---
type: verdict
title: 'Verdict: plugin-install-known-marketplace plan-reviewer round 4'
description: 'plan-reviewer verdict for round 4 of plugin-install-known-marketplace: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:45:13+00:00'
slug: plugin-install-known-marketplace
pass: plan-reviewer
round: 4
body_schema: verdict/1
---

## Summary

No open risk could break the plan. p5 is fixed by the new contract: kmctl builds
the argument from the entry, lets claude decide, and turns claude's "source
doesn't match" refusal into a PluginError naming the settings file and the entry.
r6 tests that against the real claude with the git-without-.git entry the round 3
probe refused. p1 to p4 stay resolved.

## Checked

- The plan against round 3's p5: kmctl no longer copies claude's parse rules, and
  the refusal path names the file and the entry. That covers the whole class p5
  named (no .git, self-hosted git, ssh, url on a known git host) without kmctl
  having to list them.
- Rows against the done-when list: r1 add arguments per kind with and without ref
  and the no-entry default; r2 managed precedence; r3 github path or unknown kind
  stops before claude; r6 the real git entry without .git gives a PluginError
  naming file and entry; r4 the real isolated install; r5 the existing tests.
  Each fails_when matches its item.
- Whether "source doesn't match" is told apart reliably, in the claude 2.1.300
  strings copy from round 3 (not the real ~/.claude). The text "its source
  doesn't match its extraKnownMarketplaces entry in user or managed settings" is
  one fixed cause in the admission check, kind "declaration". The other add
  failures carry other text: a network location ("on a network drive..."), a bad
  git URL ("its git URL can't be used: ..."), an unreadable url ("can't be read
  as an https:// or http:// address"), reserved or invalid names, and clone or
  fetch errors. The same cause string is used by both the pre-fetch check and the
  named check after the fetch, so a substring match catches both.
- A neighbouring refusal ("your settings list X under extraKnownMarketplaces with
  another source ... Add it from that source") has different text. If a built
  argument hit that one, kmctl would pass claude's message on, which already
  names the settings entry. That is a weaker message, not a broken plan.
- Spike plugin-install-known-marketplace/1 still covers the operator's .git case.

## Findings

- p1 resolved: github and git carry #ref.
- p2 resolved: extra fields and unknown kinds stop before claude runs.
- p3 resolved: the managed files and OS folders are named.
- p4 resolved: the last managed entry wins, tested by r2.
- p5 resolved: kmctl no longer predicts claude's parse; claude's refusal becomes
  a PluginError naming the file and entry, tested by r6 against real claude.

## Notes

The match depends on claude's wording, so a later claude could reword it. r6 runs
the real claude, so a reword fails r6 instead of slipping through. r4 and r6 need
network access to clone from GitHub, as r4 already did.
