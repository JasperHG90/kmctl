---
type: verdict
title: 'Verdict: okf-fields-invariant reviewer round 2'
description: 'reviewer verdict for round 2 of okf-fields-invariant: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:45:25+00:00'
slug: okf-fields-invariant
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three findings sent back are fixed, and f4 is fixed too. The fixes broke
nothing I could find. The gates and all five eval rows pass.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass; rows r1 to r5 pass; "stamp green: 2ff70752b38472b45360e3dbc9ed1ce41ea40fb72def408c2b9b837636f2b374".
- f1: field() now wraps a dict as one item only when the head is in `_SINGLE_MAPPING` (verified); any other non-list reads as []. This matches main's old `_sources` (non-list gives []) and `_last_verified` (single mapping wrapped, non-dict entries dropped). test_field_forms asserts both a string and a single mapping under `sources` read as [].
- f2: the assertion is now `re.search(r"I4.*enforced", log_text)`. `.` does not match a newline, so it needs both on one line. Log line 16 matches, and line 11 ("reworded I4") does not.
- f3: verified is 5.2 and okf_version is sections 8 and 12. Both agree with the vendored validator (§5.2 for verified, §12 for the root index okf_version).
- f4: `_is_front_matter_call` matches `ast.Attribute` calls with attr `front_matter`. A new test covers `okf.front_matter(p)` and then a subscript. Aliased imports of front_matter or field from kmctl.okf are flagged.

## Findings

- f1: resolved at src/kmctl/okf.py, in the `_SINGLE_MAPPING` branch of field().
- f2: resolved at tests/test_okf_fields.py, in test_manifesto_marks_i4_enforced.
- f3: resolved in ALLOWED_FIELDS in src/kmctl/okf.py.
- f4: resolved at tests/test_okf_fields.py, in _is_front_matter_call and test_reads_scan_catches_attribute_calls.
