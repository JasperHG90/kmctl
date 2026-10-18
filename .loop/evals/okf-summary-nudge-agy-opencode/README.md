---
type: eval
title: 'Eval: okf-summary-nudge-agy-opencode'
description: 'Definition of done for okf-summary-nudge-agy-opencode: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T22:04:29+00:00'
slug: okf-summary-nudge-agy-opencode
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 7b47385593cbe424ad76cc0217ae97f4fd4dcbf697fa0e39fd8703ceb551cd2d
  at: '2026-10-18T22:04:29+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl summary nudge --format antigravity, given agy's PostToolUse JSON with workspacePaths[0] naming a repository whose summary is behind and run from its .agents/ folder, prints {"injectSteps":[{"systemMessage":{"systemMessage":TEXT}}]} with TEXT naming the changed concepts and both ways out; with the summary current, or bad stdin, it prints {} and exits 0.
  Fails when: the JSON shape differs, the repository is read from the cwd (.agents/) rather than workspacePaths, TEXT lacks the concepts or the ways out, or a quiet case prints a nudge or exits nonzero
- r2: kmctl summary nudge --format opencode --path DIR reads no stdin (run with stdin left open, it returns at once), takes the repository from --path, prints the nudge text alone when the summary is behind and nothing when it is current, exiting 0.
  Fails when: it reads or waits on stdin, ignores --path, prints JSON or other text, prints when current, or exits nonzero
- r3: apm/antigravity/.apm/hooks/hooks.json carries a PostToolUse entry running KMCTL_PINNED=1 kmctl summary nudge --format antigravity with a timeout, guarded so a missing kmctl or verb prints {} and exits 0; kmctl doctor reports it, reading APM's nested {matcher, hooks} form of the entry.
  Fails when: the entry, KMCTL_PINNED, the guard or the timeout is missing, a missing verb makes it fail, or doctor does not check it
- r4: The plugin kmctl plugin patch writes to .opencode/plugins/kmctl.js registers ctx.tool.hook("execute.after"), runs kmctl summary nudge --format opencode --path <project> with KMCTL_PINNED=1 and stdin closed, asynchronously with a timeout, and appends {type: "text", text} to event.result.content only when the output is non-empty, never throwing; run under node with a fake ctx and a real child process (a fake kmctl script that would block on an open stdin), it appends the text once when kmctl prints a nudge, returns well inside the timeout, and leaves content unchanged when kmctl prints nothing, fails, or is missing; --undo removes it; kmctl doctor reports it.
  Fails when: the hook is not registered, KMCTL_PINNED or --path is not passed, stdin is left open (the fake blocks to the timeout), it appends on empty output or a failure, throws, or doctor does not check it
- r5: docs/reference/commands.md, the nudge's decision and docs/how-to/install-kmctl-with-apm.md name the Antigravity and OpenCode nudges, and the decision notes that agy documents PostToolUse as expecting {} and kmctl relies on injectSteps reaching the model there (spike 1).
  Fails when: a page does not name a harness's nudge or the decision omits the agy caveat
- r6: The full suite and every tier pass.
  Fails when: any test fails
