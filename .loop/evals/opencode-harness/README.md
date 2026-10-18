---
type: eval
title: 'Eval: opencode-harness'
description: 'Definition of done for opencode-harness: 11 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T05:00:09+00:00'
slug: opencode-harness
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: aac31a61a83c5b8ee155ef37e44e792fd8fb56f9186fa7661c38df70ec820c80
  at: '2026-10-18T05:00:09+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The OpenCode agent translator keeps description, adds mode: subagent, writes permission with "*": deny first and then allow for each mapped tool (Read to read, Grep to grep, Glob to glob, Write and Edit to edit, Bash to shell), drops name, color, effort and model, copies the body unchanged, gives the same bytes for the same input, and refuses, naming the tool, a Claude tool not in its map.
  Fails when: any mapping differs, "*": deny is not the first rule, a tools key or a Claude-only key survives, the body changes, two runs differ, or an unknown tool translates silently
- r2: In a repository whose lock shows kmctl's package installed for OpenCode, kmctl plugin patch rewrites .opencode/agents/kmctl-auditor.md, bundle-weaver.md and event-analyzer.md into the translated form (the auditor allows only read, grep and glob), writes kmctl's four rules to .opencode/rules/ without their applyTo front matter, merges ".opencode/rules/*.md" into opencode.json's instructions once while keeping every other key (mcp included), writes .opencode/plugins/kmctl.js, and writes nothing under .agents/plugins/; a second patch changes no file.
  Fails when: a file is missing, extra or differs from that description, another opencode.json key changes or is lost, the instructions entry appears twice, anything is written under .agents/plugins/, or a second patch changes a file
- r3: kmctl plugin patch refuses, naming the file, an opencode.json that is not valid JSON, and leaves it unchanged.
  Fails when: patch exits 0, names no file, or changes the file
- r4: Harnesses are told apart correctly now that .agents/skills/ is shared: a lock with only OpenCode files (.opencode/ plus .agents/skills/) reads as opencode only, one with Antigravity's rules or hooks reads as antigravity, and both read as both, in plugin.py and in doctor.
  Fails when: an OpenCode-only lock reads as antigravity, or any of the three cases gives the wrong harnesses in either module
- r5: The briefing plugin .opencode/plugins/kmctl.js, loaded under node with a stub ctx as OpenCode 2.x loads it (a default export {id, setup}; setup registers a context hook), pushes the kmctl briefing as a {type: "text"} system part, and when kmctl is not on PATH, fails or prints nothing it pushes nothing, and neither setup nor the hook throws or rejects, even with an empty ctx (I1).
  Fails when: the text pushed differs from kmctl briefing's output, setup registers no context hook, or with kmctl missing, failing or silent anything is pushed or anything throws or rejects; the test skips only when node is not on PATH
- r6: kmctl plugin patch --undo deletes the three translated agents, the four rules, the instructions entry (and opencode.json when patch created it and nothing else is left) and the plugin file, and nothing else; patch --scope user leaves OpenCode alone and says so.
  Fails when: a kmctl file is left, a file kmctl did not write is removed or changed, or --scope user writes under .opencode/ or says nothing
- r7: kmctl doctor, for an OpenCode install, runs opencode.lock, opencode.files, opencode.okf-skills, opencode.agents, opencode.rules, opencode.okf-mcp, opencode.hook and dep.opencode; after a bare apm install (agents back in Claude format), a hand-edited rule, a missing instructions entry, a missing okf-bundle entry or an edited plugin, the matching check fails with a fix naming kmctl plugin patch or apm install --target opencode; on a freshly patched install every check but dep.opencode (when opencode is not on PATH) passes; doctor's help lists the new checks.
  Fails when: any listed fault goes unreported, a fix names neither command, a clean install fails a check, or the help omits a check
- r8: In a scratch consumer, apm install --target opencode (APM 0.33.0) of kmctl's package served from a local git server, then kmctl plugin patch, leaves kmctl's and okf's skills in .agents/skills/, the four rules, the three translated agents, the plugin, and opencode.json with the instructions entry and okf-bundle as {type: local, enabled: true, command: [sh, -c, ...]}; a second apm install then kmctl plugin patch changes no file; patch --undo then apm uninstall exits 0 and leaves no kmctl or okf file.
  Fails when: any step fails, any of those is missing or differs, a reinstall plus patch changes a file, or the uninstall fails or leaves files
- r9: With OpenCode 2.x on PATH, opencode debug agents (on a service port of its own that the test stops) lists kmctl-auditor, bundle-weaver and event-analyzer as subagents; the test skips when opencode is absent.
  Fails when: opencode is present and any of the three agents is missing from its list
- r10: A new decision records the OpenCode route (APM for skills and okf's server, patch for agents, rules through instructions, and the V2 briefing plugin), the tool map, that every rule loads every session, that apm install reverts the agents so patch runs after every install and --undo runs before apm uninstall, why apm audit reports drift, and a table of the gaps with when to drop each; the manifesto names OpenCode and no longer lists it as out of scope; docs/reference/commands.md documents what patch, --undo and doctor do for OpenCode; the install how-to and README give the OpenCode install, that every rule always loads, and that okf's server needs uv.
  Fails when: any of those is missing, or the decision does not match kmctl schema decision
- r11: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
