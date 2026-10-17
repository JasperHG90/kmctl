---
type: verdict
title: 'Verdict: antigravity-okf-stop-hook-reviewer-f4 reviewer round 1'
description: 'reviewer verdict for round 1 of antigravity-okf-stop-hook-reviewer-f4: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T08:24:45+00:00'
slug: antigravity-okf-stop-hook-reviewer-f4
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. Doctor now reads .agents/hooks.json the
way install does, gives the repair-by-hand fix for a file that is not a JSON
object, and counts only a handler whose command runs okf-stop-check.sh. Two
non-blocking findings: a wording slip in the reference and an encoding crash
that existed before this change.

## Checked

- Gates: `loopctl gate stamp` from the worktree (scratch HOME) printed
  `stamp green: 0697fbc03e8f3f3199089f380bd9216905ec226767448c8a06628021aab2fec4`;
  lint, format, tests, integration, r1, r2 and r3 all passed.
- Code: read _apm_hooks_data, _okf_handlers, apm_okf_stop_present and
  drop_apm_okf_stop in src/kmctl/antigravity.py, and _antigravity_apm_hooks in
  src/kmctl/doctor.py. The only other caller (plugin.py:997) goes through
  drop_apm_okf_stop, which catches PluginError, so install cannot raise anything new.
- r1: `-k apm_hooks` selects four tests. The existing okf-handler test checks
  the fix equals AG_FIX and exit code 1, and the existing no-okf test checks
  that the check passes. The new unparsable-file test checks the detail, the
  exact repair fix and exit code 1. The new mention-outside-a-handler test
  checks that the check passes. Each of the row's fails_when cases would fail a test.
- r2: the docs test checks the sample apm-hooks line, the note's
  "okf's Stop check" and commands.md's "not a JSON object". It does not compare
  the whole note with the CLI's string, so I compared the how-to line
  with plugin.py:1001 by hand; they match.
- r3: the full suite is green in the stamp above.

## Findings

- f1: commands.md's fix column says "not JSON" while the check fails for any
  non-object. A user with a JSON list would read that install alone fixes it.
  This is a plain wording fix.
- f2: a non-UTF-8 hooks.json raises UnicodeDecodeError from read_text, which
  neither _apm_hooks_data nor its callers catch, so doctor and install crash.
  Catching UnicodeDecodeError next to JSONDecodeError would route it to the
  same repair path. This was already true before the change, and the repo's
  pre-existing-issues rule asks that it be fixed. It is a bug, but I marked it
  non-blocking because the fix is one line and needs no second review.
