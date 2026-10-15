---
type: verdict
title: 'Verdict: link-check reviewer round 2'
description: 'reviewer verdict for round 2 of link-check: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:05:46+00:00'
slug: link-check
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both findings sent back are fixed and the fixes broke nothing I could find. `_links` now takes the `_entries` result for docs/README.md and skips only the one link per line that the index check owns, so other links on an entry line are checked. The help text and module docstring name the link check. Gates and rows r1 to r5 are green.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1 to r5 pass, "stamp green: dc9d53b7415c86f6dca517a847224805b176f0fa6aaa2a33188b0059e998e6a3".
- Read the staged diff of src/kmctl/checks.py, src/kmctl/__init__.py and tests/test_check.py, plus `_entries` and the module docstring in full.
- Confirmed `_ENTRY` and `_LINK` both pick the line's first link (including after an image `!`), so the skipped link is the one `_entries` returns. When `_entries` drops the first link (it leaves the folder or starts with `/`), nothing is skipped.
- Ran `kmctl check --path` on a scratch repo whose docs/README.md had: a valid entry plus ../GONE.md and /src/old.py on the same line; a missing in-folder entry; entries ../OUT.md and /ROOT.md; an angle-bracket entry; and a line with the same valid target twice. Output: index reports line 4 (missing entry) once, with no duplicate from the link check; link reports line 3 twice, plus lines 5 and 6. Nothing was double reported and nothing was missed.
- `kmctl check --help` shows the new summary "Check indexes agree with their folders, prototypes have a README.md, and links resolve."
- The new test test_link_check_covers_other_links_on_index_lines asserts two exact (file, line) findings for the out-of-folder and `/` links on an entry line, and would fail with the round-1 skip-whole-line code.

## Findings

- f1: resolved in src/kmctl/checks.py `_links` (skip only the entry target `_entries` returns, once per line) and covered by tests/test_check.py test_link_check_covers_other_links_on_index_lines.
- f2: resolved at src/kmctl/__init__.py:118 and checks.py line 1, plus a new module docstring bullet for check name `link`.
- f3: resolved; the r3 test asserts the exact computed line (cleared earlier, confirmed here).

## Notes

The index check reports `<how-to/install.md>` as missing because `_ENTRY` keeps the angle brackets. That bug was there before this change and belongs to the deferred f4 stub, which covers other link forms. The link check handles that link correctly.
