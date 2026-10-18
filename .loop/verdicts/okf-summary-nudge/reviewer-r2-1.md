---
type: verdict
title: 'Verdict: okf-summary-nudge reviewer round 2'
description: 'reviewer verdict for round 2 of okf-summary-nudge: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T23:43:52+00:00'
slug: okf-summary-nudge
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three round-1 findings are fixed, and I checked each by hand. The new
--path fallback leaves the hook path as it was: without --path, empty or bad
stdin still prints nothing. One new non-blocking nit: the --json output is a
dict built by hand rather than a dataclass passed through asdict, which is
what the repo's other verbs do and what the boundaries rule asks for. A plain
fix is enough, so no new review round is needed.

## Checked

- I re-ran `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r6 all pass; "stamp green: b511cadabb0c18b62f07a88245301a2965078e6863cfde8c919b86a928e62933".
- I read summary_nudge in src/kmctl/__init__.py, Nudge, nudge and payload_cwd in src/kmctl/summary.py, the new and changed tests in tests/test_summary_nudge.py, the summary nudge section of docs/reference/commands.md, and the explanation paragraph.
- Logic: root starts as `path or Path(".")`. Stdin replaces it when it names a cwd. A payload with no cwd keeps it. BadPayload re-raises only when path is None, and then the outer except stays quiet. That matches the help, the epilog and commands.md.
- I tested by hand in a scratch repo made with kmctl init plus kmctl new decision. `kmctl summary nudge --path REPO --json </dev/null` from / printed behind true, the concept id and the nudge. A repeat printed nudge null with behind still true. `--json` with no --path and empty stdin printed the quiet object and exited 0. A payload with no cwd under `--format claude` printed {}, because the set had already been named. `--json --format claude` exited 2 and named both options.
- Tests: test_nudges_with_an_explicit_path_and_unusable_stdin covers each unusable stdin with --path. test_quiet_on_unreadable_or_empty_stdin still covers r2 without --path. The JSON tests check the shape on a nudge, a repeat, a current repo and a failure, plus the refused pair.
- The rule and practice for the dict: .claude/rules/pydantic-boundaries.md and the other --json verbs in __init__.py, which use json.dumps(asdict(...)) at lines 127, 334, 454, 817 and others. The one dict precedent, `schema --json`, prints a name-to-purpose map with no fixed record shape.

## Findings

- f1: resolved. __init__.py:909 to 916 fall back to an explicit --path on BadPayload, and the tests and my manual run confirm it.
- f2: resolved. The --json option, the refusal with --format claude, the help text and the commands.md row are all in place.
- f3: resolved. The explanation page now tells the two hooks' failure output apart.
- f4: open, nit, non-blocking. The JSON is assembled inline at __init__.py:921 to 929. Move the shape into the Nudge dataclass (add behind) and print asdict(found), like the sibling verbs.

## Notes

Nothing else changed outside what the fix summary lists.
