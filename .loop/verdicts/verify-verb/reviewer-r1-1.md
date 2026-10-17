---
type: verdict
title: 'Verdict: verify-verb reviewer round 1'
description: 'reviewer verdict for round 1 of verify-verb: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T21:38:38+00:00'
slug: verify-verb
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The verb works for the common forms: it clears unverified, same-day-source and stale concepts and docs pages, extends block, unindented, single-mapping and flow forms, and refuses cleanly. Two bugs block. A CRLF file is converted to LF throughout (f1), and '..' in the id gets past the handoff refusal and reaches any .md file under the repository root through the docs/ prefix (f2). Two smaller points do not block: the reference page leaves out some refusals (f3), and a trailing comment on the verified line gets a misleading refusal (f4).

## Checked

- `loopctl gate stamp` from the worktree: every gate passed (lint, format, tests, integration) and so did eval rows r1 to r8 and r10. Stamp green: 49450a38c2e6c49484df0a32f90a11aa933463adf64d6f5edc30ab27e95584df.
- I read src/kmctl/verify.py, the __init__.py diff, tests/test_verify.py, the new tests in tests/test_review_due.py, and the rule, skill, ADR and docs diffs.
- I ran a probe script against temporary repositories: CRLF file (f1), a comment on the verified line (f4), a comment inside an item (works), verified before sources (works, sources kept), a blank line inside the list, a flow list (written at values are quoted strings and still clear review due), traversal ids (f2), stale_after mid-file with --stale-after (replaced in place, rest kept), an id with .md, no front matter, a BOM (refused as having no front matter; safe).
- Eval rows: r1 asserts that review due no longer lists the id, the entry's by, a full timestamp (the unverified params have only the new at, so a bare date would fail there) and the log line. r2, r3 (the by order and the lines outside the block), r4 (exit 1, empty stdout, one stderr line, the fix text, no file changed), r4b, r5, r6 (Next line present and absent, JSON keys) and r7 each assert their fails_when. r4b checks stale_after is more than 150 days out, not the exact time; that is weak but enough.
- r9 (judgment): ADR 0023 says the verb records a person's check, that an agent runs it only when the named person has read and asked, never on an audit verdict alone, and that ADR 0005 and I2 stand. commands.md has a section for the verb, and the overview's Depicts list names `kmctl verify` and `verify.py`. The row holds.

## Findings

- f1 (bug, blocking): CRLF files lose their line endings. The plan and the docs promise every other line stays as it was. Fix: read and write with newline='' (or bytes) and keep the file's line ending, plus a CRLF case in the keeps test.
- f2 (bug, blocking): the traversal ids above verify a handoff and README.md. The plan says a handoff is refused. A wrong fix here would ship the same hole, so I want to see it again.
- f3 (docs, not blocking): the reference page's refusal list and output line are incomplete.
- f4 (hardening, not blocking): a comment on the verified line gets a refusal that gives the wrong fix.

## Notes

When a block list has a blank line between items, _block stops at the blank, so the new entry goes in before the later items rather than last. review due takes the latest at, so the id still clears. Blank lines inside a front matter list are rare.
