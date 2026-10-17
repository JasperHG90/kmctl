---
type: verdict
title: 'Verdict: real-audits reviewer round 1'
description: 'reviewer verdict for round 1 of real-audits: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T16:36:09+00:00'
slug: real-audits
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks: `Report` has `checked`, findings carry
claim, contradicted_by and fix, read ranges and search hits are recorded, an
output validator sends bad citations back with `ModelRetry`, and the run
stops with exit 1 and no report.json when retries run out. Gates are green.
One hole in the evidence check blocks: a reversed range citation is accepted
without being checked at all, which defeats the "code must" guarantee the
plan is about.

## Checked

- Ran `loopctl gate stamp` from the worktree: lint, format, tests,
  integration and eval rows r1 to r4 all pass; "stamp green:
  2e16a537bf5919ec741de78b3ad9f5f697f95c95420388db2a9394c567a12c60".
- Read the full uncommitted diff (agent.py, tests, ADR 0017, how-to,
  overview, log) and the surrounding read_file, search_files, resolve and
  run code.
- r1: test_report_shape_lists_checked_after_findings asserts checked in
  report.json, the three finding keys, and the checked entry after the
  findings in report.md; the summary file equals report.md in the existing
  test. Asserts the fails_when.
- r2: test_evidence_unread_lines_are_sent_back covers a line outside the
  range read, a file never read, a line past the end and a malformed cite,
  asserts each is named in the retry and the corrected report is written;
  the search-hit test covers hits. Asserts the fails_when.
- r3: the CLI TestModel test asserts exit 1, the "citations could not be
  checked" message and no report.json. Probed with a FunctionModel that
  always cites an unread line: PydanticAI raises after 6 reports, so it
  cannot loop past the limit.
- r4: the prompt test checks both shipped prompts for the new wording and
  the absence of "holds is info".
- r5 (judgment): the ADR 0017 correction, the how-to paragraph and the
  overview diagram edge each say that holds go in checked, findings are
  mismatches only, and citations of unseen lines go back to the agent. A
  reader would not expect info findings for things that hold. Passes,
  apart from the off-by-one in f2.
- Probed bad_citations directly on a 20-line file with nothing read.

## Findings

- f1: `bad_citations` takes `first` and `last` from the regex and checks
  `range(first, last + 1)`. For `f.md:15-3` or `f.md:99-1` that range is
  empty, `last` is within the file, so nothing is flagged; my probe
  returned no error for either, though nothing was read and line 99 is past
  the end of a 20-line file. Reject `first > last` (and `first < 1`) with a
  message saying so, and add the case to the evidence test.
- f2: `retries={"output": 5}` allows five retries, so six reports in all;
  "after 5 tries" in the stderr message, "After five tries" in the ADR
  correction and "after five tries" in the how-to undercount by one. Say
  "sent back five times" or similar.
- f3: update the `render` docstring to mention the checked list.

## Notes

`ws.unchecked` is not cleared when a later output fails for another reason
(for example a schema error after a citation retry), so the give-up message
could blame citations for a different failure. Worth resetting it at the
start of the validator only if that matters; not a finding.
