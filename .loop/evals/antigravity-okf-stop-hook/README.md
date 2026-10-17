---
type: eval
title: 'Eval: antigravity-okf-stop-hook'
description: 'Definition of done for antigravity-okf-stop-hook: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:48:01+00:00'
slug: antigravity-okf-stop-hook
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 0a15a4acdd6f4beeef17fcab390e86a895ce90ad54b86364f20168ec74a867ea
  at: '2026-10-17T06:48:01+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The plugin folder's hooks.json holds two named hooks: kmctl-briefing (unchanged) and kmctl-okf-stop with one flat Stop handler. Run by hand with the plugin folder as its working folder, the handler prints {"decision": "continue", "reason": okf's reason} when stdin says executionNum 0, the repository's .okf/index.md sets upkeep: enforced and a tracked file outside .okf/ changed; it prints {} on executionNum 1, when nothing outside .okf/ changed, and when okf's script is missing or fails; it always exits 0.
  Fails when: a hook is missing or extra, the handler is not flat, it continues on executionNum 1 or for a clean tree, it prints anything but JSON, it exits nonzero, or the reason differs from okf's
- r2: kmctl plugin install --harness antigravity takes every Stop handler whose command names okf-stop-check.sh out of .agents/hooks.json, drops a named hook left with no handlers, keeps every other hook and key, and leaves the file valid JSON; a missing .agents/hooks.json is left missing; a second install changes nothing.
  Fails when: an okf handler remains, another hook or key is lost or changed, an empty named hook remains, the file stops parsing, a missing file is created, or a second install changes a file
- r3: kmctl doctor fails a check naming .agents/hooks.json and kmctl plugin install --harness antigravity when that file still runs okf-stop-check.sh, passes it otherwise, and antigravity.hook passes only when the plugin folder's hooks.json holds both hooks as this kmctl writes them.
  Fails when: the okf handler in .agents/hooks.json goes unreported, the check names no fix, it fails without one, or antigravity.hook passes with a hook missing or changed
- r4: With agy on PATH, agy plugin validate --strict --json on the written folder reports hooks 2 and no findings; in a scratch consumer installed from a local git server (APM 0.33.0), .agents/hooks.json runs no okf-stop-check.sh and kmctl doctor exits 0.
  Fails when: validate reports a finding or a hook count other than 2, the consumer's .agents/hooks.json still runs okf's script, or doctor exits nonzero
- r5: A decision (amending ADR 0015) records why kmctl owns okf's Stop hook for Antigravity (APM's path relative to the wrong folder, the working folder, block versus continue, executionNum counting from 0 per turn), and docs/reference/commands.md and the install how-to describe the kmctl-okf-stop hook and the doctor check.
  Fails when: the decision or either page lacks the hook, or the reference lacks the doctor check
- r6: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
