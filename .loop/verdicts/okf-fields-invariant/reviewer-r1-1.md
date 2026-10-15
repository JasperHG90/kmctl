---
type: verdict
title: 'Verdict: okf-fields-invariant reviewer round 1'
description: 'reviewer verdict for round 1 of okf-fields-invariant: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:39:25+00:00'
slug: okf-fields-invariant
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. All front matter reads in src/kmctl go
through okf.field. The writes test runs every writing verb and checks the
keys. The link regexes now follow CommonMark's angle-bracket rule. The gates
are green. There are four non-blocking findings: field() now accepts more
sources forms than before, the log check in r5 cannot fail, two section
citations are wrong, and the reads scan misses attribute calls. Each has a
simple fix that does not need another review.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass; rows r1 to r5 pass; "stamp green: a4bd7051...".
- I read the full staged diff (the changes are staged, not committed) and checked every front matter read: grep shows front_matter called only in concepts, supersede, handoffs and review_due, and each result goes into field().
- r1: the test runs init, new for each kind, new handoff with --key twice, new decision, decision supersede and new doc in tmp_path. It collects nested paths from every .okf and docs page and asserts they are a subset of ALLOWED_FIELDS. An unknown key written by any of these verbs would fail it.
- r2: I ran _bad_reads on probe sources. It flags `meta.get` after assignment, annotated assignment, walrus, tuple unpacking and keyword use. It misses `okf.front_matter(...)` and aliases (f4).
- r3: the test covers verified as one mapping and as a list, sources with string and mapping items, generated.at, defaults, and KeyError on an unknown key. A probe shows the non-list sources forms behave differently (f1).
- r4: under the old regexes `[x](<a>b.md>)` fell back to the plain target `<a>b.md>`, and `[r]: <a>b.md>` matched `<a>`, so both were reported. A probe of the new regexes: `[x](<a>b.md>)` gives no match, `<ok.md>`, `plain.md "t"`, `[r]: <ok.md> "t"` and `[r]: plain.md` still resolve, and `[r]: <a>b.md>` gives no match.
- r5: the manifesto marks I4 enforced and names the test, and the strict validator runs. The log assertion is weak (f2).
- review_due's helper refactor, the dataclasses.field rename and the handoffs tuple reshaping keep the old behaviour (same defaults for title and description, same sort keys).
- I compared the section citations against tests/vendor/okf/okf_validate.py (f3).

## Findings

- f1 (bug, non-blocking): the `[value] if value` wrap in field() applies to every [] path, not only verified. Non-blocking because it only reads malformed (non-list) sources more leniently, and the fix is plain: limit the single-mapping wrap to verified and keep non-list sources as [], or keep the new behaviour and document and test it.
- f2 (test-strength, non-blocking): the log line exists, so nothing is wrong today. Tighten the regex to require I4 on the same line, for example `I4.*enforced`.
- f3 (docs, non-blocking): fix the two citations (verified to 5.2, okf_version to 12).
- f4 (test-strength, non-blocking): also match `ast.Attribute` calls whose attr is `front_matter`. No current code escapes the scan.

## Notes

The manifesto rule asks that an enforced invariant's test drive kmctl from
outside. The reads half is a source scan, as the signed plan chose. The
writes half drives the CLI.
