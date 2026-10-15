---
type: verdict
title: 'Verdict: handoffs-list reviewer round 2'
description: 'reviewer verdict for round 2 of handoffs-list: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:41:54+00:00'
slug: handoffs-list
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are fixed. One bad handoff is now skipped with a stderr warning naming the file, the rest are still listed, and --json stdout stays one clean list. Offset timestamps now print in UTC. Skipping is the right choice over refusing: /continue reads the --json list to resume work, and refusing would block every handoff because of one bad file. The fixes broke nothing in rows r1 to r4. Two small non-blocking items remain: an overflow edge case that the astimezone fix added (f3), and an untested branch (f4).

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1 to r4 pass. Stamp green: f164bc963fc5e87154d495afed1d24c267bc28b720ef855e9ce873cc499c7bb4.
- Read src/kmctl/okf.py, src/kmctl/handoffs.py, the handoffs command in src/kmctl/__init__.py and tests/test_handoffs.py in full.
- f1: test_handoffs_skip_bad_front_matter_with_a_warning parses result.stdout as JSON while the warning goes to stderr. It asserts the good and odd handoffs are listed, and that broken.md is named on stderr. By hand: a Latin-1 file was skipped with "not UTF-8 text" on stderr, stdout stayed valid JSON, and the exit code was 0.
- f2: test_handoffs_dates_are_converted_to_utc checks that +02:00 09:00 prints as 07:00Z. Ordering is unchanged, because aware datetimes already compared correctly.
- By hand: generated.at "0001-01-01T00:00:00+01:00" crashes with OverflowError from astimezone (f3).

## Findings

- f1: resolved. front_matter raises BadFrontMatter for bad YAML and for non-UTF-8 text. live_handoffs catches it, appends a warning and continues, and reads generated.at only when generated is a dict (src/kmctl/handoffs.py:52-60). The command prints each warning to stderr before the output.
- f2: resolved. as_datetime converts aware values with astimezone(UTC) (src/kmctl/okf.py:43), and a test covers it.
- f3: open, hardening, non-blocking. The astimezone call added for f2 overflows near datetime.min or datetime.max. This is the same class of crash as f1, but only a contrived timestamp triggers it. A plain fix is enough: catch OverflowError in as_datetime and return None, so the value counts as unreadable. It does not need my second look.
- f4: open, test-strength, non-blocking. Add a test that writes non-UTF-8 bytes and asserts the file is skipped with a warning. The code already works, as my probe showed, so the test only guards against regressions and does not need review again.
