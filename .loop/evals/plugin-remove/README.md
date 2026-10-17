---
type: eval
title: 'Eval: plugin-remove'
description: 'Definition of done for plugin-remove: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T07:25:30+00:00'
slug: plugin-remove
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 72e1b4d007d0ee0fe45e240d774e0de9d91f55d7a6d28ae9b51101af069933d0
  at: '2026-10-17T07:25:30+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl plugin remove takes --harness, --scope and --json like install; without --harness it asks at a terminal with the installed harnesses (doctor's harnesses_found) as the default, and refuses without a terminal or with --json, naming --harness; with nothing installed it says so and exits 0 without running APM.
  Fails when: an option is missing, the question or its default differs, a run without a terminal prompts or exits 0 without --harness, or a run with nothing installed runs APM or exits nonzero
- r2: Removing every installed harness runs uvx --from apm-cli==0.33.0 apm uninstall NAME (-g at user scope), where NAME is HOST[:PORT]/OWNER/REPO/apm built from the kmctl apm.yml entry's git: URL with its case kept (a plain string entry is passed as is); it runs no apm install afterwards.
  Fails when: the uninstall name differs from that rule for an https GitHub URL, an http host:port URL or a string entry, -g is missing at user scope, or an install runs
- r3: Removing some installed harnesses uninstalls kmctl's entry and then installs the kept harnesses alone from the removed entry's git: source at its ref (not this CLI's version); if that install fails, remove exits 1 naming APM's cause, that the kept harnesses were uninstalled, and kmctl plugin install --harness KEPT --source SOURCE with a note that it installs at this kmctl's version.
  Fails when: the reinstall uses another source or ref, targets the removed harness, or a failed reinstall exits 0 or names no fix
- r4: For claude, remove takes kmctl's SessionStart hook out of the settings file (other keys and hooks kept) and kmctl's okf-bundle entry out of .mcp.json (claude mcp remove --scope user okf-bundle at user scope), leaving an okf server kmctl did not write; for antigravity it deletes .agents/plugins/kmctl/ and an .agents/hooks.json that is {}; a removed harness leaves apm.yml targets: only when no other dependencies.apm entry is left, and otherwise a note says the target was kept and that a bare apm install would deploy kmctl to it again.
  Fails when: a kmctl piece remains for a removed harness, another key, hook, server or file is lost, a target is dropped while another dependency remains or kept when none does, or the kept-target note is missing
- r5: doctor's harnesses_found counts apm.yml targets only when the lock lists no kmctl package, so after a partial remove doctor reports only the kept harness; remove ends with a Next: kmctl doctor line; a second remove changes nothing.
  Fails when: doctor reports a removed harness as installed after a partial remove, the Next line is missing, or a second remove runs APM or changes a file
- r6: In a scratch consumer installed for claude and antigravity from a local git server (APM 0.33.0), kmctl plugin remove --harness antigravity leaves claude whole (doctor's claude checks pass) and nothing of kmctl under .agents/; kmctl plugin remove --harness claude then leaves no kmctl file, hook, MCP entry or lock, with the consumer's other files untouched.
  Fails when: either remove fails, a kmctl or okf file, hook, MCP entry or lock entry remains for a removed harness, claude breaks after the first remove, or another file changes
- r7: kmctl plugin remove --help names what it removes, its options and examples; docs/reference/commands.md documents it; the install how-to says how to remove kmctl; a decision records how remove works and why (uninstall then reinstall the rest, the target rule).
  Fails when: the help, the reference, the how-to or the decision lacks remove
- r8: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
