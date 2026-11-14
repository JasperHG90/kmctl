---
type: eval
title: 'Eval: kmaudit-mcp'
description: 'Definition of done for kmaudit-mcp: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:22:55+00:00'
slug: kmaudit-mcp
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 6dcde8a260c963d56fa1b3ac0ebbb4df909f2fe66de6f7a7a43788b0d0d79d41
  at: '2026-11-14T17:22:55+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: `kmaudit mcp`, started through the MCP SDK's stdio client in a fixture repository, lists the tools namespaces, claims_todo, claims_submit, claims_list, checks_todo, checks_try, checks_submit, checks_run, checks_list, coverage and judge, each taking folder.
  Fails when: the server does not start over stdio, a tool is missing, or a tool other than namespaces takes no folder
- r2: Through the tools, a claims_todo, claims_submit and claims_list round trip for one namespace stores and reads back the claims, returning the JSON the CLI's --json prints.
  Fails when: submit stores nothing, list does not show the submitted claims, or a result's fields differ from the CLI's --json for the same call
- r3: A refused call (a stale key, an unknown folder) comes back as an MCP tool error whose text is the CLI's refusal line naming the fix; the server keeps running.
  Fails when: a refusal returns as a success, the error text lacks the fix, or the server exits
- r4: claims_todo with its default limit on a folder of 200 pending sections returns under 25,000 tokens (bytes / 4), and brief leaves out the instructions; `kmaudit claims todo --brief` does the same on the CLI.
  Fails when: the default result is 100,000 bytes or more, or brief still carries the instructions
- r5: Every tool the server lists is named in packages/kmaudit/docs/commands.md, and packages/kmaudit/README.md has a section for each of Claude Code, Codex, Antigravity and LangGraph saying how to add the server.
  Fails when: a listed tool is missing from the docs, or any of the four harnesses has no section
