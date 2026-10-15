---
type: verdict
title: 'Verdict: plugin-install-known-marketplace reviewer round 2'
description: 'reviewer verdict for round 2 of plugin-install-known-marketplace: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:56:26+00:00'
slug: plugin-install-known-marketplace
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three findings sent back are fixed and the fixes break nothing nearby. A broken entry is now skipped the way claude skips it, the dot-file test can fail, and os is imported normally. The open question about later broken files only matters in an edge case where the add still succeeds or kmctl stops with a clear message, so it does not block.

## Checked

- Read the staged plugin.py diff in full and the new and changed tests (test_okf_source_skips_dot_files, test_okf_source_ignores_broken_entry, _isolated_home).
- `loopctl gate stamp` from the worktree: lint, format, tests and rows r1-r6 all pass, `stamp green: 3b402a99a9899a4f14d48e676fa53d46a1e6827c0be8a436e9b22f2547fa83b3`.
- f1: `_usable` returns False for a non-dict entry, a non-dict `source`, a non-string kind, and a known kind without a string location. That covers the four shapes claude 2.1.300 ignored in my round 1 probes ({}, string source, no repo, plus no kind). Unknown string kinds (npm) still count as entries and reach the PluginError, which matches claude refusing them. The new test checks each shape alone (expects OKF_SOURCE, None) and as a later managed drop-in over a good managed-settings.json (expects the earlier entry). Without `_usable` both asserts fail.
- f2: the dot-file is now the only file in managed-settings.d. Without the filter, `.hidden.json` would be read last and `hidden/okf` would win, so the assert fails. Row r1's `-k okf_source` runs this test.
- f3: `import os` at the top of the test module; `_isolated_home` uses `os.environ`.
- Fallback probe (scratch review-mkt-r2): I tried putting the broken entry in a project `.claude/settings.local.json` over a user entry. claude's mismatch check says it reads only "user or managed settings", and every case refused because of the user entry. So that layer cannot answer the question, and managed files need root, so I did not probe it.

## Findings

- f1: resolved at src/kmctl/plugin.py:124 (`_usable`), with test_okf_source_ignores_broken_entry.
- f2: resolved at tests/test_plugin_install.py:280.
- f3: resolved at tests/test_plugin_install.py:8.

## Notes

The fallback question does not change the outcome in practice. Case: a good earlier managed entry and a broken later one. If claude drops the broken file or entry and keeps the earlier one, kmctl matches it exactly. If claude merges first and then ignores the broken merged value, claude has no entry and accepts any add, so kmctl's add from the earlier source still succeeds. They only differ when the earlier entry is one kmctl cannot carry (for example npm): kmctl would then stop with a clear message naming the file, even though claude might have accepted the default add. That needs two managed files to disagree, one broken, so it is not worth a round. A `ref` that is not a string, or an empty location string, still passes `_usable`; claude's handling of those is unprobed and they are unlikely in real settings.
