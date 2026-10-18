---
type: eval
title: 'Eval: okf-summary-nudge'
description: 'Definition of done for okf-summary-nudge: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:56:19+00:00'
slug: okf-summary-nudge
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 73b46e30f7a6b81c9e243e41a98d1a2a7a0ae4efdd258439714644e2b942ecbf
  at: '2026-10-18T21:56:19+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl summary nudge --format claude, given a PostToolUse payload on stdin for a repository whose summary is behind (a concept changed after the summary), prints one JSON object with hookSpecificOutput.hookEventName PostToolUse and an additionalContext naming the changed concepts and both ways out (update .okf/summary.md, or kmctl summary ack); it exits 0.
  Fails when: nothing is printed when the summary is behind, the JSON lacks the fields, the concepts or either way out are not named, or it exits nonzero
- r2: The nudge is quiet ({} and exit 0) when the summary is current, after an edit to the summary or an ack, when only log.md, an index, a handoff or the summary changed, when the same changed set was already nudged about (a new concept in the set nudges again), outside a git repository, with no .okf/, and on unreadable or empty stdin; it never writes under .okf/. The hook command sets KMCTL_PINNED=1 for the call, so in a project whose apm.lock.yaml pins another kmctl release no copy calls uvx; run with a fake kmctl that lacks the verb (exits 2 with a usage error), the hook command prints {} and exits 0.
  Fails when: any quiet case prints a nudge, a repeat set nudges twice, a grown set does not nudge, it exits nonzero, or a file under .okf/ changes, the hook command does not set KMCTL_PINNED=1, uvx is called for a project pinned to another release, or the hook command fails or prints anything but {} when the verb is missing
- r3: The nudge decides with git only: its path never calls review_due (patched in the test to raise), so it stays cheap enough to run after every matching tool call (the freshness rule takes 24 to 54 ms here, spike:okf-summary/1).
  Fails when: the nudge calls review_due on any path
- r4: apm/claude/.apm/hooks/hooks.json carries a PostToolUse entry with matcher Write|Edit|MultiEdit|Bash whose command runs kmctl summary nudge --format claude, guarded like the SessionStart hook so a missing kmctl prints {} and exits 0, with a timeout; kmctl doctor reports the entry in .claude/settings.json (claude.nudge-hook) and its fix when missing.
  Fails when: the entry, matcher, guard or timeout is missing, a missing kmctl makes the command fail, or doctor does not check it
- r5: A decision supersedes ADR 0004 (written with kmctl decision supersede), invariant I1 in .okf/manifesto.md names both hooks and that neither blocks, and docs/explanation/why-one-hook-and-report-only-audits.md, docs/reference/commands.md and .okf/architecture/overview.md describe the nudge hook.
  Fails when: ADR 0004 is not marked superseded by the new decision, I1 names only SessionStart, or a page does not describe the nudge
- r6: The full suite and every tier pass.
  Fails when: any test fails
