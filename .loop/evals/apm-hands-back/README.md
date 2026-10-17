---
type: eval
title: 'Eval: apm-hands-back'
description: 'Definition of done for apm-hands-back: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T13:01:22+00:00'
slug: apm-hands-back
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: ecc0b84b4c97d42e9704d80eed1aa3faa8e571dbbf1b8e028a5731dc2e5df144
  at: '2026-10-17T13:01:22+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: apm/apm.yml lists the pinned okf-skills, ./claude and ./antigravity under dependencies.apm and okf-bundle under dependencies.mcp (stdio, command sh, args [-c, the launcher plugin.okf_mcp_launcher() builds for the pinned okf commit]); apm/claude/apm.yml has targets [claude], the four rules in .apm/instructions and .apm/hooks with one SessionStart hook equal to plugin.hook_entry(); apm/antigravity/apm.yml has targets [antigravity], the four rules and .apm/hooks with one SessionStart hook running antigravity.HOOK_COMMAND and one Stop hook running the okf Stop wrapper for a hooks.json in .agents/; the shared .apm/ keeps the skills and kmctl-auditor and holds no instructions.
  Fails when: any entry, target, file or command differs, the MCP launcher's okf commit differs from the okf-skills pin, a sub-package has no .apm/ folder, or instructions remain in the shared package
- r2: The Antigravity rules are generated from the Claude rules by scripts/sync_antigravity_rules.py: same names and bodies, applyTo written as one single-quoted string of the globs, each with a **/ prefix, joined by escaped commas; the committed copies equal its output, and --check exits 1 naming the stale file when they differ.
  Fails when: a generated rule differs from the committed one, a glob lacks **/ or a comma is not escaped, a body differs, or --check passes on a stale copy
- r3: kmctl plugin install writes no SessionStart hook, no okf-bundle (no .mcp.json write and no claude mcp add-json) and nothing under .agents/ but the plugin folder, which holds only plugin.json and the translated agents; it still takes APM's okf Stop handler (bash ".agents/hooks/okf-skills/hooks/okf-stop-check.sh") out of .agents/hooks.json and keeps kmctl's Stop wrapper and every other hook.
  Fails when: install writes a hook, an MCP entry, rules, hooks.json or mcp_config.json itself, the plugin folder holds anything but plugin.json and agents, APM's okf handler stays, or the wrapper or another hook is removed
- r4: Before running APM, install removes what an older kmctl wrote that APM now writes, at project and user scope: a SessionStart group running kmctl briefing that the scope's apm-hooks.json does not record, and an okf-bundle entry whose args differ from the package's (in .mcp.json, or at user scope via the user .claude.json); every other hook, key and server stays.
  Fails when: an unrecorded kmctl group or a stale okf-bundle remains, APM's recorded group or an identical okf-bundle is removed, or another hook, key or server changes
- r5: kmctl doctor passes for an install whose hooks, rules and MCP entries APM wrote: claude.hook and claude.okf-mcp read the files APM writes; antigravity.hook checks .agents/hooks.json holds kmctl's SessionStart and Stop wrapper; antigravity.okf-mcp checks .agents/mcp_config.json; antigravity.plugin checks plugin.json and the agents only; antigravity.files covers kmctl's rules in .agents/rules/ again; each failure names apm install or kmctl plugin install.
  Fails when: a complete APM-delivered install fails a check, a missing APM-delivered piece passes, or a fix names no command
- r6: In a scratch consumer served from a local git server (APM 0.33.0), kmctl plugin install --harness claude,antigravity leaves the SessionStart hooks, rules and okf-bundle recorded by APM (its apm-hooks.json sidecars and the lock's mcp_servers), the plugin folder with only plugin.json and agents, and doctor passing; apm uninstall of the entry then leaves only the plugin folder of kmctl's; and an install over a consumer set up the old way (kmctl-written hook and okf-bundle) leaves exactly one kmctl SessionStart hook.
  Fails when: a piece is not APM's, doctor fails, uninstall leaves another kmctl file, or two kmctl hooks remain
- r7: A new decision records that APM delivers the hook, okf's MCP server and the per-harness rules through sub-packages, supersedes ADR 0016, amends ADRs 0014, 0015 and 0018, and lists what APM cannot do yet (Antigravity agents, issue #2990; okf's Antigravity Stop path; apm uninstall -g leaving okf-bundle; an allowExecutables block blocking the hook and server; a second okf server for users with their own), each with its stopgap and when to drop it; the commands reference, both install how-tos and the architecture page describe the new split.
  Fails when: the decision lacks a listed gap or the supersede and amend links, or a page still says kmctl writes the hook, the MCP server or the Antigravity rules
- r8: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
