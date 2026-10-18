---
type: verdict
title: 'Verdict: okf-summary reviewer round 1'
description: 'reviewer verdict for round 1 of okf-summary: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T20:38:57+00:00'
slug: okf-summary
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change mostly does what the plan says. The kind, the skeleton, the 500-word
check, the commit-order rule, review due, the warning in check and CI, the
briefing line inside the budget, the I4 extension and this repo's summary are
all there and tested. One blocking bug remains: `kmctl summary ack` turns into
a silent no-op that still reports success when the summary already carries
today's `checked` for the same ids, so a concept changed twice in one day
cannot be cleared with ack (f1). There are three non-blocking issues: the
briefing points to a summary that may not exist (f2), and some docs are now
false (f3, f4).

## Checked

- Read the diff of src/, tests/, .okf/ and docs/ against HEAD (the
  `main...HEAD` diff also holds unrelated .loop moves on main), and read
  summary.py and tests/test_summary.py in full.
- Ran `loopctl gate stamp` from the worktree (result quoted in Notes).
- Eval rows: r1 to r7 map to `-k` selections in tests/test_summary.py,
  test_briefing.py and test_okf_fields.py. Each test drives the CLI and
  asserts the row's fails_when: headings, the index link, strict okf
  validation, 500 passes and 501 fails with the count, every concept kind,
  same commit, a later commit, working tree, untracked, log, index, handoff
  and stray prototype files, shallow clone, no git, ack's exact byte diff
  touching one file only, check exit 0 with a warning, and the CI action
  report. r4's tests miss the same-day re-ack case (f1).
- Ran by hand in scratch repos: kmctl update on an old bundle (warns, then
  check fails on the unlisted summary: judgement call 1, f4); the briefing
  with no summary.md (f2); ack then strict okf validation (conformant);
  the tutorial flow (outputs other than step 2 still hold); a verify stamp
  (lists the summary, as the ADR expects); and f1's repro.
- Worst-case briefing (3 live handoffs, a clipped title, 103 due, summary
  behind by 100): 494 tokens, 1,973 characters, as ADR 0027 says.
- This repo: .okf/summary.md has a 428-word body (wc on the whole file,
  front matter included). Strict okf validation passes, and kmctl check
  passes. Its claims match the bundle: no practices/proposals/prototypes
  folders, I2 is planned, the out-of-scope list matches the manifesto, and
  the ADRs it cites are not superseded.

## Findings

- **f1** (blocking): ack is a no-op that reports success when the `checked`
  block it would write is already there. A fix has to make ack always
  change the summary, or make the rule honour `checked.against`. Either way
  it touches the freshness contract, so it needs another look. Add a test:
  ack, commit, change the same concept again, commit, then ack must clear.
- **f2**: fall back to `.okf/index.md` in ROUTING when there is no summary.
  It is a plain change, but keep the worst-case budget test green.
- **f3**: update the tutorial's init output and reader-start sentence, the
  okf-bundle instruction in both harness copies, and README.md's "Working on
  kmctl" line.
- **f4**: correct ADR 0027's upgrade consequence and document the manual
  index line for `kmctl update`.

## Notes

- Judgement call 1: leaving the kept index.md alone and only warning follows
  ADR 0011 and the manifesto case exactly. CI breaks only after a user runs
  `kmctl update` and commits without the index line, and the pre-commit hook
  catches that first. I accept it. Only the docs are off (f4).
- Judgement calls 2 to 4 (ack writes nothing when current and refuses
  without git; the briefing leaves the state out when it cannot tell; a
  stale summary is a warning) follow the plan and are documented. I accept
  them.
- Judgement call 5: summary.py imports verify.py's private `_block`. It
  works, and the gates allow it. A later cleanup could make it public in
  okf.py. Not a finding.
- Judgement call 6: the dated Correction appended to ADR 0011 matches how
  the repo amends records, and its index entry says so. Fine.
- `loopctl gate stamp` from the worktree: every gate (lint, format, tests,
  integration) and eval rows r1 to r8 passed; "stamp green:
  747378898beaf67e2b46e28d09007349b9f097710d88150e57086805888528fb". A green
  r4 does not cover f1.
