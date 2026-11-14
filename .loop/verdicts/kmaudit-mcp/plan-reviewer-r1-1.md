---
type: verdict
title: 'Verdict: kmaudit-mcp plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-mcp: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:25:26+00:00'
slug: kmaudit-mcp
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works. The SDK is there (mcp 2.3.0 on PyPI exposes MCPServer and ToolError), it resolves in the shared root lock, and the spike answers the size risk. Three things need a revision before building, none a rethink. judge is not the thin verb the plan says it is (p1). The tool-error contract is unclear when a submit is only partly refused (p2). The folder contract assumes every harness starts the server in the repository (p3).

## Checked

- Spike kmaudit-mcp/1. I read the README, stdout.txt and run.json: exit 0, run on a worktree, and the store copied rather than opened. The figures back the paging change: about 277k tokens with no limit, about 41k at limit 15, about 5k for checks todo at limit 5 with brief.
- Every verb the plan names, in verbs.py, check_verbs.py, coverage.py, judge.py and namespaces.py, and each CLI --json path in cli.py. All but judge are a call plus model_dump_json. namespaces dumps dataclasses with json.dumps, and checks try uses a TypeAdapter. checks todo already has brief; claims todo does not.
- The dropped uv.lock risk. In a scratch copy of the root pyproject, kmaudit's pyproject and uv.lock, I added mcp>=2.3.0 to kmaudit and ran uv lock. It resolved and added mcp, mcp-types, starlette, uvicorn, sse-starlette, pyjwt and a few more, with no conflict against the pinned dev group. I agree with dropping the risk.
- The MCPServer API in a scratch venv with mcp 2.3.0: it has tool, run_stdio_async and mcpserver.exceptions.ToolError.
- Problems, Goals and Outcomes against the prose. P1 and P2 are separate causes. O1 is a behaviour that can ship alone, and O2 is support that needs O1's tool list. O1's touches cover the claims todo brief flag (cli.py, verbs.py) but not judge.py (see p1).

## Findings

- p1: judge's logic lives in the CLI command body and calls asyncio.run, so the server cannot wrap it thinly. The plan has to name the extraction and the tool's inputs, or drop judge from this ticket.
- p2: a partly refused submit cannot be both a tool error and the CLI's JSON as r2 and r3 are written. The contract must say what the agent gets.
- p3: folders relative to the working directory, and the harnesses' tool timeouts, may not hold for every harness G1 promises. Allow absolute folders and have the README say what each harness needs.

## Notes

- The plan's "5 sections is about 14k tokens" is an average. The largest section is 26k bytes, so five large sections could pass 25k tokens. r4 uses a 200-section fixture and will not see that. Not blocking, but brief and the default limit may need to cap by size as well as by count.
- Subprocesses in steps.py, anchors.py and namespaces.py capture output but inherit stdin, which is the MCP channel in a stdio server. The calls I saw (git, CLI --help) do not read stdin, but stdin=DEVNULL costs nothing. A build detail, not a finding.
- The sync verbs (checks run, mutation testing) will block the server's event loop unless MCPServer runs them in a thread. A build detail.
