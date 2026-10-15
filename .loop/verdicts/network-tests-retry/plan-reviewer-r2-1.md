---
type: verdict
title: 'Verdict: network-tests-retry plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of network-tests-retry: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T19:13:46+00:00'
slug: network-tests-retry
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved: every install or update now asserts its result with the output, and spike 1 shows that output carries git's "Could not resolve host" into the pytest report. One new contract problem: r5 asks every install or update call to assert exit 0, but two install calls in the file are meant to fail. Fail, for a one-line fix to r5 and the Done-when text.

## Checked

- Spike network-tests-retry/1 (README, stdout.txt, run.json, exit 0): with github.com rewritten to an unresolvable host, claude's stderr ends with git's `fatal: unable to access ...: Could not resolve host`, `_require` (src/kmctl/plugin.py:184) keeps that last line, kmctl's message carries it, and the asserted pytest reports of test_install_pulls_okf and test_update_after_bump show it. That settles the plan's listed risk for a DNS failure on the okf marketplace add.
- Untested cases the spike names (connection refused or timed out, a network error at a later step): these do not break the plan. The retry fails safe. A network error it does not recognise is reported at once, which is today's behaviour, never a false pass. Of the later steps, `marketplace update kmctl` and `marketplace add <folder>` (plugin.py:268-271) use the local staged folder, so they make no network call. `plugin install kmctl@kmctl` (plugin.py:275) goes through the same `_require`, so a git line would come through the same way. The worst case is claude timing out git itself and printing only its own "Network error or timeout" line. That is a missed retry, not a broken plan.
- Rows against Done-when: r1 matches "default collects none, the gate runs all" and "unregistered marker fails collection". r2 matches the three retry cases plus p1's later-surfacing case. r3 matches "every test that adds the okf marketplace carries the marker". r4 is the overall pass. r5 matches only the intent bullet: no Done-when item names it (p2).
- tests/test_plugin_install.py: the six tests named in the plan do ignore their first install result (lines 85, 94, 125, 158, 175, 191). Lines 195 and 362 are install calls that expect a non-zero exit.

## Findings

- p1 (resolved): the asserted results carry claude's last stderr line into the failure report, and the spike confirms the wording the retry matches.
- p2 (test-mismatch, blocking, r5): "every install or update call asserts exit_code == 0" contradicts `plain = _kmctl("plugin", "install", ...)` at line 195, which must exit 1, and the refused-entry install at line 362, which must exit non-zero. Limit r5 to calls expected to succeed (or require the exit to be asserted, with the output, whatever value is expected), and add it to Done-when.

## Notes

- In test_installed_version_check_after_upgrade, a network error on the `plain` install would also exit 1. The next assert (`"run kmctl plugin update" in plain.stderr`) would fail and show plain.stderr, so the network text still reaches the report and the retry still works.
