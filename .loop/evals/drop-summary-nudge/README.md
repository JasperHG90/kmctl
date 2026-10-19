---
type: eval
title: 'Eval: drop-summary-nudge'
description: 'Definition of done for drop-summary-nudge: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-19T05:22:25+00:00'
slug: drop-summary-nudge
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 392cbce6f600ab317462076ee16dc1d149e0bac8b53f17c06d95a0cd11596f4f
  at: '2026-10-19T05:22:25+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The Claude and Antigravity packages' hooks.json hold only kmctl's SessionStart hook (Antigravity also keeps its okf Stop check), and the OpenCode plugin kmctl writes has no execute.after hook.
  Fails when: any shipped hooks.json has a PostToolUse entry, or the OpenCode plugin source contains execute.after
- r2: kmctl summary nudge no longer exists (kmctl summary --help lists only ack) and kmctl doctor has no nudge-hook check for any harness.
  Fails when: kmctl summary nudge exits 0, the summary help lists nudge, or doctor --json has a check id ending in nudge-hook
- r3: Nothing under src/, apm/, docs/ or README.md mentions the nudge, and a decision supersedes ADR 0028, restoring the one-hook rule, with I1 naming one hook.
  Fails when: grep -ri nudge matches in those paths, ADR 0028's status is not deprecated, or no decision says it supersedes ADR 0028
- r4: The full suite and every tier pass.
  Fails when: any test fails
