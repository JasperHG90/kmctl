---
type: verdict
title: 'Verdict: kmaudit-mcp plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmaudit-mcp: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:27:47+00:00'
slug: kmaudit-mcp
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The revisions close all three round 1 findings. judge gets a shared async function in judge.py. A whole-call refusal is a tool error, and a mixed batch returns the --json result with its refused list. folder may be absolute, and the README covers each harness's working directory and timeout. One new mismatch remains, and it is small: the stdin=DEVNULL change touches three files that O1's touches leave out (p4). Nothing I found would make the approach fail.

## Checked

- Round 1 verdict plan-reviewer-r1-1 and each of its ids against the revised plan and the re-signed eval rows r1 to r5.
- p1: judge.judge (judge.py:422) is already async and takes a Store, Settings, a question, ids and lines. The setup that has to move is the body of audit_judge (cli.py:704 to 800): the question and tenacity checks, loading settings, reading lines, opening the store, asyncio.run and splitting answers from failures. The plan names that move and the per-id result, and judge.py is in O1's touches.
- p2: verbs.submit (verbs.py:335) raises AuditError only for input that is not JSON, an empty list or an unknown bundle. Everything per item, a stale key included, goes into refused. That matches the split between whole-call and mixed batch, and r3.
- p3: resolve_target takes absolute and relative paths. r5 checks an absolute folder, and the plan has the README name each harness's working directory and timeout.
- Running verbs in a thread is safe for the store. Each verb opens its own Store inside the call, so a sqlite connection never crosses threads. No verb module writes to stdout (only cli.py and ui.py print), so nothing outside the protocol reaches the MCP channel. None of mutate.py, check_verbs.py or verbs.py starts a process beyond the subprocess.run calls listed in p4.
- Spike kmaudit-mcp/1 still answers the size risk, as in round 1. The plan is unchanged there.
- Problems, Goals and Outcomes against the prose. O1 is a behaviour that can ship alone, and O2 is support that needs O1. P1 and P2 are separate causes. The touches cover cli.py, verbs.py (claims todo --brief) and judge.py, but miss the subprocess files (p4).

## Findings

- p1 resolved: the judge extraction is named, with its inputs and its per-id result.
- p2 resolved: whole-call refusal versus mixed batch is now a clear contract, and r3 tests it.
- p3 resolved: absolute folders, off-loop slow verbs, and the README's per-harness working directory and timeout.
- p4 open: stdin=DEVNULL changes anchors.py, namespaces.py and steps.py, which are not in O1's touches.

## Notes

- The prose names "a stale key" as a whole-call refusal, but in code a stale key is refused per item, and r3 treats it that way (one good and one stale answer stores the good one). Follow r3. A batch where every item is stale should still return the result with an empty stored list, not an error.
- ui.py:631 also calls asyncio.run(judge(...)). It can keep doing so, since the UI does not run inside the server's loop, or switch to the new function. Either works.
- judge does its sqlite reads and writes on whichever thread awaits it. If the tool runs it on the loop thread, it should open its Store there too, which the new function does when it takes the folder.
