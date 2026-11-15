---
type: eval
title: 'Eval: kmaudit-mcp'
description: 'Definition of done for kmaudit-mcp: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:26:26+00:00'
slug: kmaudit-mcp
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 60cff99e83c650963be518500d22604843881c35c4d16090729dd9306bcc46e3
  at: '2026-11-14T17:26:26+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: `kmaudit mcp`, started through the MCP SDK's stdio client in a fixture repository, lists the tools namespaces, claims_todo, claims_submit, claims_list, checks_todo, checks_try, checks_submit, checks_run, checks_list, coverage and judge, each taking folder. judge takes folder, question, ids and lines and returns one entry per id; the CLI's `kmaudit judge` awaits the same function in judge.py.
  Fails when: the server does not start over stdio, a tool is missing, or a tool other than namespaces takes no folder, or judge's tool and CLI command do not share one function
- r2: Through the tools, a claims_todo, claims_submit and claims_list round trip for one namespace stores and reads back the claims, returning the JSON the CLI's --json prints.
  Fails when: submit stores nothing, list does not show the submitted claims, or a result's fields differ from the CLI's --json for the same call
- r3: A whole-call refusal (an unknown folder, an input that does not parse) comes back as an MCP tool error whose text is the CLI's refusal line naming the fix, and the server keeps running; a submit batch with one good and one stale answer stores the good one and returns a result whose refused list names the stale one and its fix.
  Fails when: a whole-call refusal returns as a success, the error text lacks the fix, the server exits, or the mixed batch is an error, stores nothing, or does not list the refused item
- r4: claims_todo with its default limit on a folder of 200 pending sections returns under 25,000 tokens (bytes / 4), and brief leaves out the instructions; `kmaudit claims todo --brief` does the same on the CLI.
  Fails when: the default result is 100,000 bytes or more, or brief still carries the instructions
- r5: Every tool the server lists is named in packages/kmaudit/docs/commands.md, and packages/kmaudit/README.md has a section for each of Claude Code, Codex, Antigravity and LangGraph saying how to add the server; an absolute folder works the same as a relative one.
  Fails when: a listed tool is missing from the docs, or any of the four harnesses has no section, or an absolute folder is refused
