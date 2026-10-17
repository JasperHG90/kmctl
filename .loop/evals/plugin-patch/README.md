---
type: eval
title: 'Eval: plugin-patch'
description: 'Definition of done for plugin-patch: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T14:48:05+00:00'
slug: plugin-patch
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: ccfe1e8aee4a508d5ce03c3d88249bb808b27f587bdc917f44f121eca2a15b18
  at: '2026-10-17T14:48:05+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl plugin patch reads apm.lock.yaml (~/.apm/ with --scope user) and, for antigravity, writes .agents/plugins/kmctl/ (plugin.json and the translated agents) and takes APM's okf Stop handler out of .agents/hooks.json; for claude, takes out a kmctl SessionStart group APM does not record and an okf-bundle differing from the package's (project files, or the user settings.json and .claude.json) and the old kmctl@kmctl plugin, saying to run apm install again when it removed something APM should write; it never runs APM or needs uv; a second run changes nothing; it ends with Next: kmctl doctor and takes --json.
  Fails when: patch runs uvx or apm, writes anything else, misses a piece for an installed harness, touches a harness the lock does not list, leaves an unrecorded kmctl group or stale okf-bundle, omits the apm install note after a removal, changes a file on a second run, or lacks the Next line or --json
- r2: Without a kmctl package in the lock, patch refuses (exit 1) naming the apm install to run; for an older entry form (the ADR 0013 string entry in apm.yml, or a lock with virtual_path plugin) it refuses before that, naming the exact apm uninstall for that entry, the {git: ..., path: apm, ref: vVERSION} entry to write and apm install.
  Fails when: patch exits 0 without a kmctl package, names no fix, or for an old form says only to run apm install or names the wrong uninstall
- r3: kmctl plugin patch --undo deletes .agents/plugins/kmctl/ and nothing else, and exits 0 when it is already gone.
  Fails when: --undo leaves the folder, deletes or changes any other file, or fails when there is nothing to undo
- r4: kmctl plugin install, update and remove no longer exist (kmctl plugin lists only patch), and the harness question goes with them; every doctor fix names apm install, the apm.yml ref or kmctl plugin patch, never kmctl plugin install, update or remove; kmctl init's Next line points at installing the package (the README's install section) rather than kmctl plugin install.
  Fails when: an old verb still runs, kmctl plugin lists another verb, a doctor fix or kmctl init's Next line names an old verb
- r5: The README has an install section per harness (Claude Code, Antigravity, both): the apm.yml entry at the CLI's version, the apm install --target line (with APM through uvx --from apm-cli==0.33.0 when it is not installed), kmctl plugin patch, trusting the folder in Antigravity, upgrading (change the ref, apm install, kmctl plugin patch) and removing (apm uninstall, kmctl plugin patch --undo, and claude mcp remove okf-bundle --scope user after a user-scope uninstall); docs/reference/commands.md documents kmctl plugin patch and no old verb; the how-tos and architecture page follow; a decision records that APM installs and kmctl patches, superseding ADR 0019 and amending ADR 0014.
  Fails when: the README lacks a harness, a step or the user-scope note, a page still documents install, update or remove, or the decision or its links are missing
- r6: In a scratch consumer, apm install of kmctl's entry from a local git server (APM 0.33.0) followed by kmctl plugin patch makes kmctl doctor pass for claude and antigravity; kmctl plugin patch --undo then apm uninstall of the entry leaves no kmctl file under .claude/ or .agents/ but files APM leaves empty.
  Fails when: patch fails, doctor exits nonzero, or a kmctl file remains after undo and uninstall
- r7: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
