---
type: verdict
title: 'Verdict: schema-verbs reviewer round 2'
description: 'reviewer verdict for round 2 of schema-verbs: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T05:29:30+00:00'
slug: schema-verbs
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed. The decision kind now carries a `then` pattern for dated Correction sections, the schema emits it as `x-kmctl-then` and names it in the description, supersede writes its heading from the same constant, and a test runs a real supersede and checks both records against the schema. The fix broke nothing I could find.

## Checked

- Gates, run by me in the worktree: `uv run pytest -q` gave 357 passed, 10 deselected. `uv run ruff check` gave all checks passed. `uv run ruff format --check` gave 71 files already formatted. `loopctl gate stamp` passed every gate (lint, format, tests, integration) and rows r1 to r6: "stamp green: cc4e938c6c95ccb1f27e5eaecb777f221ca29c0203976afd2948b3cba7ed6090".
- `src/kmctl/kinds.py`: `CORRECTION`, `DocumentKind.then`, the decision's pattern `Correction, \d{4}-\d{2}-\d{2}`, `_body_text` and `schema()`. `x-kmctl-then` appears only for decisions; `kmctl schema practice` has none. The pattern matches what supersede writes, `now.date().isoformat()`.
- `src/kmctl/supersede.py`: the heading and the status word now come from `kinds`. The new record gets a plain paragraph with no heading, so its sections stay at the fixed three.
- `tests/test_schema.py`: `_check` takes the fixed prefix and then needs every remaining heading to fullmatch the `then` pattern. The supersede test runs init, new decision and supersede through the CLI, checks that a Correction heading was written, and checks both records. The stray-section test shows that a trailing `## Notes` fails. The shape test lets `x-kmctl-then` appear only beside a list body, and only as `{"pattern"}`. The r3 selector `-k matches_what_kmctl_writes` picks up both new tests.
- `docs/reference/commands.md` describes `x-kmctl-then` correctly. The manifesto description now says the operator may change the sections, which covers my round 1 note.

## Findings

- f1: resolved at src/kmctl/kinds.py:134 (the `then` pattern), src/kmctl/supersede.py:121 (the constant) and tests/test_schema.py:218 (the supersede test).

## Notes

The stray-section test is named `test_schema_matches_what_kmctl_writes_on_a_stray_section`, but kmctl never writes that file. The name exists so the r3 selector picks the test up. It reads oddly but does no harm.
