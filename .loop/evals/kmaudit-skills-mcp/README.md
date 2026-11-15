---
type: eval
title: 'Eval: kmaudit-skills-mcp'
description: 'Definition of done for kmaudit-skills-mcp: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T06:38:58+00:00'
slug: kmaudit-skills-mcp
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: c3a5370590be6b5c782b407354e0a126ed993501f62e81127ea7527433318aaa
  at: '2026-11-15T06:38:58+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit's APM package holds the extract-claims and write-checks skills and declares the kmaudit MCP server as uvx from its own kmaudit-vX.Y.Z tag; its Claude-only sub-package (packages/kmaudit/apm/claude, targets: [claude]) holds kmaudit-claims-extractor and kmaudit-check-writer, whose tools are Read, Grep, Glob and the five kmaudit MCP tools, with no Bash and no hook.
  Fails when: a skill or agent is missing from kmaudit's package, the server is not declared at the package's own tag, an agent has Bash or a hook, or the sub-package targets more than claude
- r2: kmctl's package, its wheel and its Antigravity and OpenCode translations no longer carry the two skills or agents, and kmctl's own audit skill and kmctl-auditor stay.
  Fails when: kmctl's package, wheel or plugin patch still holds or translates them, or loses its own audit skill or auditor
- r3: release.py set --package kmaudit pins the MCP server's ref to the release tag with the version.
  Fails when: the server's ref keeps an old tag after set
- r4: Installing kmaudit's package with APM for claude and opencode puts the kmaudit server in .mcp.json and opencode.json, the two agents in .claude/agents/ and none in .opencode/agents/.
  Fails when: the server is missing for a harness, the agents are missing for Claude Code, or OpenCode receives agent files
- r5: The skills' evals and the repository's skills tests pass for the moved skills, which name the MCP tools and say what to do where no agent exists.
  Fails when: a skill test fails, or a skill still names a kmaudit shell command
