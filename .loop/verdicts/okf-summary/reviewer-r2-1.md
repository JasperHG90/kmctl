---
type: verdict
title: 'Verdict: okf-summary reviewer round 2'
description: 'reviewer verdict for round 2 of okf-summary: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T21:04:27+00:00'
slug: okf-summary
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All four round-1 findings are fixed. f1 is fixed: ack now writes `checked.at`
as a UTC timestamp to the second, and moves one second on if that would
leave the bytes unchanged. That means a same-day re-ack always changes the
summary and clears it. The operator-ruled change also holds: init and update
link a new summary or manifesto from a kept root index and log it, insert
exactly one line in the right place, touch nothing else, and do nothing on a
second run. Two small issues remain, neither blocking. ADR 0011 does not
record the new kept-file exception (f5), and the init output contradicts
itself when the log is not UTF-8 (f6).

## Checked

- Ran `loopctl gate stamp` from the worktree. Lint, format, tests and
  integration passed, and so did eval rows r1 to r8: "stamp green:
  de477ed5e0a1a10e0a292c638fff5c12ffe670b84a97cb5a890c1e8dd7fff25c".
- f1: read `ack` and `_with_checked`. Reran round 1's repro by hand: init,
  commit; new decision, ack, commit; edit that decision, commit; ack. The
  summary changed (git status M). After commit, review due no longer lists
  the summary, and `kmctl check` passes. The vendored strict OKF validator
  says the acked bundle is conformant. The new tests
  `test_clears_ack_again_after_the_same_concept_changes_again` and
  `..._in_the_same_second_...` sit under r4's `-k clears`. They assert that
  the bytes change and that the reasons clear, so they would fail on the old
  code.
- f2: ROUTING_NO_SUMMARY is picked when `.okf/summary.md` is not a file.
  The briefing test covers it.
- f3: read the diffs of the tutorial, both okf-bundle instruction copies,
  .claude/rules/okf-bundle.md and README.md. AGENTS.md:77 says
  "`.okf/decisions/` (start at `.okf/index.md`)" in answer to "why a choice
  was made". The root index still links the decisions section, so that line
  is still true and needs no change.
- f4: ADR 0027:97-102 and commands.md:95-121 now describe what update does.
- The operator-ruled linking: read `_insert_entry` and `_link_new_pages`.
  Ran by hand in scratch repos:
  - A kept index with an intro, a wrapped entry and a trailing paragraph got
    exactly two lines, summary then manifesto, before the first entry. The
    diff showed nothing else changed, and the log got dated lines.
  - A second init changed no file (diff -r), and its JSON was empty apart
    from skipped.
  - An index with no entries and no final newline got the entries appended
    on new lines.
  - A non-UTF-8 index or log was left alone with a warning naming it.
  - ADR 0027's consequence and commands.md describe this. ADR 0011 does not
    (f5).

## Findings

- **f1** resolved: src/kmctl/summary.py:217-223, which steps a second on when
  the bytes would repeat. Tests in tests/test_summary.py:353-396.
- **f2** resolved: src/kmctl/briefing.py:59 and :214.
- **f3** resolved: the tutorial, README, both instruction copies and the
  repo rule.
- **f4** resolved: ADR 0027's update consequence and commands.md's init
  section.
- **f5** (docs, not blocking): ADR 0011's list of kept-file exceptions, and
  README.md:112, do not mention the new index and log edit.
- **f6** (nit, not blocking): the `linked` line claims a log line was written
  even when the warning says it was not.

## Notes

- After a log-line warning (log not UTF-8), a later update will not add the
  line, because the page already exists by then. The warning says to add it
  by hand, which is enough.
- The init output says "and the first decision's" for the root index. If the
  kept index already linked decisions/, the root index got no decision
  entry, so the claim is slightly loose. This wording was there before the
  change. Not a finding.
