---
type: verdict
title: 'Verdict: handoffs-list reviewer round 1'
description: 'reviewer verdict for round 1 of handoffs-list: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:38:39+00:00'
slug: handoffs-list
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The listing, ordering, filtering, JSON shape and empty case match the plan, and every eval row's test asserts its fails_when. Two bugs remain. One malformed handoff file crashes the whole command (f1, blocking). A non-UTC generated.at shows the wrong date (f2, a one-line `.astimezone(UTC)` fix plus a test, which I trust without a second look).

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, and rows r1 to r4 pass. Stamp green: b06faa8700ab6dfa9b0bee720e82cdefdd6a360443eee06564f0c9f1ddc25132.
- Read the staged diff (pyproject.toml, uv.lock, src/kmctl/__init__.py) and all of src/kmctl/handoffs.py, src/kmctl/okf.py and tests/test_handoffs.py.
- r1: test_handoffs_order checks the full id order, including an a/b tie written in reverse order. r2: test_handoffs_filtering checks expired left out, no stale_after kept, index.md skipped, by exact list equality. r3: test_handoffs_json checks all five keys by exact dict equality, and [] for a root with no handoffs folder. r4: test_handoffs_none checks exit 0 and the message.
- Probed by hand in the scratchpad. A +02:00 generated.at printed as Z with the local hour (f2). `title: [bad` raised a yaml ScannerError traceback, and `generated: yesterday` raised AttributeError (f1).
- `kmctl handoffs --help` renders within 80 columns, with a metavar example for --path and examples in the epilog. Against ADR 0008: newest first, expired handoffs left to review due.

## Findings

- f1: front_matter calls yaml.safe_load with no error handling, and live_handoffs calls `.get` on `generated` without checking its type. One bad file in .okf/handoffs/ stops the listing for every handoff. Refuse with one stderr line naming the file (per the a-refusal-names-the-fix rule), or skip it with a warning on stderr. Either way, add a test. It is blocking because choosing between those behaviours, and keeping stdout clean for --json, needs a second look.
- f2: in src/kmctl/okf.py, `as_datetime` returns an aware value as it is. Ordering and has_passed still compare correctly, because aware datetimes compare across offsets. But `_date_text` formats with a literal Z, so the date shown is wrong. Convert with `.astimezone(UTC)` and add a test with an offset timestamp. Non-blocking, because the fix is one line and a test.

## Notes

The has_passed docstring says review-due uses it. review-due does not exist yet. That is the planned follow-up, so I am not raising it as a finding.
