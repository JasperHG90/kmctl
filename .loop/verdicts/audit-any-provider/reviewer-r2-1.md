---
type: verdict
title: 'Verdict: audit-any-provider reviewer round 2'
description: 'reviewer verdict for round 2 of audit-any-provider: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T15:21:47+00:00'
slug: audit-any-provider
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed. Search now splits the decoded text on "\n" only and strips trailing "\r", the same way read_file counts lines, so the two tools give the same number for the same line. The fix broke nothing I could find, and the gates are green on my own run.

## Checked

- Code: search_files at action/hermes/kmctl-read/__init__.py:196-201 splits on "\n" and calls rstrip("\r"); read_file at :157 strips "\n" and then every trailing "\r". Both strip all trailing CRs, so they agree on CRLF and on "\r\r\n" too.
- Probe (a new script in my scratch folder): form feed with a lone CR, CRLF, U+2028 with \x85, \x0b with \x1c, "\r\r\n", and no final newline. In every file, search and read gave the same line number for `target`. A CRLF search result has no stray "\r". The size cap still cuts at 2,000,000 bytes and says so, and the 200-match cap still stops the search.
- Round 1 probe re-run: every path escape is still refused, along with NUL and surrogate paths, FIFOs, folders and missing or relative roots. Binary and 5 MB files still read within the cap. `--pre=rm` and `(a+)+$` still match as plain text in 0.02 s. The results match round 1.
- Test: test_search_and_read_agree_on_line_numbers writes `a\x0cb\nc\rd\ntarget\n` and asserts `odd.txt:3:` from search and `3|target` from read. splitlines() would give 5, so the test fails on the old code.
- Gates: `loopctl gate stamp` from the worktree: lint, format and tests pass, and r1 to r7 pass. Result: `stamp green: 6c0d32c702ad2bf049d0c789d3181ff63595c0c7ce07dd747208472bdd0da762`.

## Findings

- f1: resolved at action/hermes/kmctl-read/__init__.py:196-199, covered by tests/test_hermes_plugin.py::test_search_and_read_agree_on_line_numbers.

## Notes

- Round 1's side remark still stands but is not a finding: read_file numbers a line longer than 100 KB as two lines, while search counts it as one. That only matters for lines above 100 KB, which are rare in a knowledge bundle.
