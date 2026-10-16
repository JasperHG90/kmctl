---
type: eval
title: 'Eval: antigravity-harness'
description: 'Definition of done for antigravity-harness: 9 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev173+ga4f6ce93a.d20261016
  at: '2026-10-16T20:25:35+00:00'
slug: antigravity-harness
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: bd3b2ef24ca62dbb444831bddd55174349998877f1e16622e214c3dc81654791
  at: '2026-10-16T20:25:35+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The agent translator maps Read, Grep, Glob, Write, Edit and Bash to view_file, grep_search, find_by_name (plus list_dir), write_to_file, replace_file_content and run_command; adds subagent: true, mainAgent: false, model: inherit, and commandExecutionPolicy: "off" only for an agent without Bash; drops color, effort and a named model; copies the body unchanged; and refuses, naming the tool, a Claude tool not in its map.
  Fails when: any mapping differs, a Claude-only key survives, the body changes, an agent with Bash gets commandExecutionPolicy off or one without gets anything else, or an unknown tool translates silently
- r2: kmctl plugin install --harness antigravity writes .agents/plugins/kmctl/ holding plugin.json {"name": "kmctl"}, hooks.json with one named hook holding one flat SessionStart handler running kmctl briefing --format antigravity, agents/kmctl-auditor.md (read-only tools, commandExecutionPolicy off), okf's bundle-weaver.md and event-analyzer.md translated from the okf-skills package APM installed, and mcp_config.json declaring the server bundle through uv run of the okf_mcp.py raw URL at the okf-skills sha apm/apm.yml pins, through the shared sh launcher that walks up from $PLUGIN_ROOT/../../.. (when set) and then from the working folder to the first folder holding .okf/; a second install leaves every file byte for byte the same.
  Fails when: a file is missing, extra or differs from that description, the MCP sha differs from apm/apm.yml's pin, or a second install changes a file, or the launcher, run from the plugin folder with PLUGIN_ROOT unset and from a repository subfolder, does not resolve the repository's .okf/
- r3: kmctl briefing --format antigravity prints {"injectSteps": [{"systemMessage": {"systemMessage": TEXT}}]} where TEXT equals the text briefing; it takes the repository from workspacePaths[0] of the JSON on stdin, run from any folder, and falls back to --path when stdin is a terminal, empty or not that JSON; text stays the default format and --json keeps its meaning.
  Fails when: the output is not that JSON, TEXT differs from kmctl briefing --path REPO, a stdin workspacePaths is ignored, the fallback fails, or the default output changes
- r4: The Antigravity hook command prints {} and exits 0 when kmctl is not on PATH and when kmctl briefing fails, so the hook never blocks and never prints non-JSON (I1).
  Fails when: the command exits nonzero or prints anything other than JSON in either case
- r5: kmctl plugin status (or its successor, per apm-only-install) with the antigravity harness reports each missing, extra or edited file under .agents/plugins/kmctl/ as a problem naming kmctl plugin install --harness antigravity.
  Fails when: a hand-edited, deleted or added file in that folder goes unreported, or the problem names no fix
- r6: With agy on PATH, agy plugin validate --strict --json on the written .agents/plugins/kmctl/ reports agents 3, hooks 1, mcpServers 1 and no findings; the test skips when agy is absent.
  Fails when: agy is present and the counts differ or any finding is reported
- r7: In a scratch consumer, kmctl plugin install --harness antigravity against the tree served from a local git server (APM 0.33.0) leaves kmctl's 7 and okf's skills in .agents/skills/, the 4 rules in .agents/rules/, and the plugin folder of r2.
  Fails when: the install fails or any of those is missing
- r8: A new decision records the Antigravity route (APM for skills and rules, a kmctl-owned plugin folder for agents, hook and MCP, the tool-name map, why agy plugin install of okf was rejected, that the folder must be trusted); the manifesto names Antigravity and no longer lists it as out of scope; ADR 0003 points to the new decision; docs/reference/commands.md documents --harness antigravity and --format; the install how-to says how to install for Antigravity, to trust the folder and that okf's MCP server needs uv.
  Fails when: any of those is missing, or the decision does not match kmctl schema decision
- r9: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
