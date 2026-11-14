---
type: verdict
title: 'Verdict: kmaudit-mcp reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-mcp: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T18:03:15+00:00'
slug: kmaudit-mcp
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `kmaudit mcp` serves the eleven tools over stdio. Each tool takes `folder`, and the todo tools page with a default limit of 5 and take `brief`. Whole-call refusals come back as tool errors carrying the CLI's refusal line, and a mixed submit batch comes back as a result with a `refused` list. The judge setup moved into `run_judge` in judge.py, and the CLI and the tool both await it. Every subprocess kmaudit starts now gets `stdin=DEVNULL`. Gates and all five eval rows pass. I found one non-blocking docs inaccuracy, so the label is fix.

## Checked

- Ran `loopctl gate stamp` in the worktree. Lint, format, tests, integration and eval rows r1 to r5 all passed: "stamp green: 626f0ac7f2c2a4a5b962170548babf3aa86aba82eeee991c97ad5a9615a2bc8d".
- Read the full diff and the new mcp_server.py and test_mcp.py.
- r1: the test starts the real `kmaudit mcp` binary through `stdio_client`, checks the tool set exactly, and checks that `folder` appears in every schema and is required for every tool except namespaces. The shared-function test monkeypatches `kmaudit.judge.run_judge`, and both the CLI and the tool import it at call time. If either side stopped using it, `seen` would hold one entry instead of two and the test would fail, so it asserts the fails_when.
- r2: the test compares the tool JSON with in-process CLI `--json` output for todo (limit 15), list and list --claims after a real submit, and checks that the stored section ids match.
- r3: an unknown folder and garbled JSON each return is_error with the CLI refusal text and the fix. Later calls in the same session succeed, so the server kept running. The mixed batch stores the good answer and refuses the stale one ("stale key", "run kmaudit claims todo"). A batch of only stale answers returns an empty `stored` list.
- r4: on 200 or more pending sections, the default result has 5 sections and is under 100,000 bytes. `brief` drops the instructions on both the tool and the CLI.
- r5: every listed tool is named in docs/commands.md, the README has a heading for each of the four harnesses, and an absolute folder gives the same result as a relative one.
- Searched src/ for subprocess, Popen and stdin reads. All four `subprocess.run` calls now pass DEVNULL. The only `sys.stdin` reads are in CLI command bodies, which the server does not reach.
- Deviations: (1) judge on the event loop: its slow part is async httpx and its sync parts are small sqlite reads, so this is acceptable and avoids nesting `asyncio.run`. Only the docs text is off (f1). (2) The judge tool returns `{entries}` while the CLI keeps its output: the plan asks for one entry per id, and commands.md documents the difference, so acceptable. (3) `answers` as a list or JSON text, and no config argument on judge: within the plan's scope, and settings still load from the default path or env. (4) `exclude_none` under brief matches what `checks todo --brief` already does, and the `--brief` help documents it. (5) The extra match of r1's `-k lists` on the refusal test is harmless. (6) I did not verify the README harness details against vendor docs. The commands look plausible and no row depends on them.

## Findings

- f1 (docs, non-blocking): commands.md line 344 ("The verbs run in a worker thread") and the mcp_server.py module docstring (line 12) say every verb runs in a worker thread. `judge` does not: it awaits on the event loop and only its HTTP calls are async. Say that judge awaits its async calls on the loop instead.

## Notes

The README's LangGraph example uses `langgraph.prebuilt.create_react_agent`, which newer LangGraph releases deprecate in favour of `langchain.agents.create_agent`. It still works, and nothing here asks for a change.
