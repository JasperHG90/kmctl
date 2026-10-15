---
type: verdict
title: 'Verdict: network-tests-retry plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of network-tests-retry: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T19:14:41+00:00'
slug: network-tests-retry
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p1 and p2 are resolved. No open risk could break the plan. Pass.

## Checked

- p2: r5's behavior now reads "asserts its expected exit code with the command output, including the two calls meant to fail", and the Done-when ends with the same item. In tests/test_plugin_install.py the only install or update calls that expect failure are line 195 (`plain`, asserted `== 1` at 201 without output) and line 362 (asserted `!= 0` at 364 without output), the two the plan names. Every other install or update call either already asserts `== 0, ...output` or is one of the six bare calls the plan lists (85, 94, 125, 158, 175, 191). `plugin status` calls are outside the item and stay so.
- Rows against Done-when: r1 covers "default run collects none, the integration gate runs all" and "unregistered marker fails collection". r2 covers the three retry cases. r3 covers "every test that adds the okf marketplace carries the marker". r5 covers the exit-code assertions. r4 is the overall pass of both tiers. Every Done-when item has a row and every row traces to one.
- The listed risk is still settled by spike network-tests-retry/1 (checked in round 2). The revision does not touch it.
- The plan hash matches the round 3 binding (c8f75a9a...).

## Findings

- p1 (resolved): every install or update result is now asserted with its output, so a network error reaches the report.
- p2 (resolved): r5 and the Done-when ask for the expected exit code, not exit 0, and the two failing calls keep their nonzero exit.
