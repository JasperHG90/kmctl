---
type: verdict
title: 'Verdict: review-hardening reviewer round 1'
description: 'reviewer verdict for round 1 of review-hardening: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:02:40+00:00'
slug: review-hardening
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

Four of the five fixes are right and their tests check the rows. The new reference-definition check also matches footnote definitions (`[^label]: text`). GitHub renders those, and kmctl check now reports the first word of the footnote text as a broken link. That is a new false error on valid docs, so the change fails.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1 to r5 all pass, stamp green 42a8984baed561a5a62e1eab958d5b5d714a0942b69462f284235a0d8b89f9b5.
- Read the staged diff (the change is staged, not committed, on loop/review-hardening) and the code around it in scaffold.py, okf.py, checks.py, grade.py and the four test files.
- r1: the test writes a non-UTF-8 kept index and asserts exit 0, no exception and "not UTF-8" on stderr. Before the fix read_text raised, so it would fail.
- r2: the test uses `0001-01-01T00:00:00+01:00`, which YAML loads as an aware datetime whose astimezone overflows, and runs both `handoffs` and `review due`, asserting exit 0 and no exception.
- r3: the test covers `?plain=1` and `<my page.md>` index entries and percent-encoded, query, angle-bracket, single-quote and double-quote targets in a page. It asserts no findings, which also catches an unlisted page if an entry fails to parse.
- r4: the test asserts the broken `[x]: missing.md` definition is a link finding at line 6, and that a `- [Other][o]` list item does not list other.md (an index finding remains).
- r5: the test runs grade.py on a free folder name joined through eval_metadata.json, a folder with no metadata and one with a wrong prompt. It asserts grading only for the first and a skip report for the others.
- By hand: ran `kmctl check` from the worktree on a scratch repo whose page has `[^1]: A footnote here.`. It reported `error link docs/how-to/p.md:5 link to A does not exist`.
- Consistency: the checks.py module docstring now describes the target rules and the reference-definition rule, and grade.py's usage docstring names eval_metadata.json. Neither contradicts the code.

## Findings

- f1 (bug, blocking): `_REF_DEF = ^ {0,3}\[[^\]]+\]:\s*(<...>|\S+)` matches `[^1]: A footnote here.`, and `_links` then checks `A` as a path. Footnotes are valid GitHub Markdown, and main does not flag them. Leave out labels that start with `^` (for example `\[(?!\^)[^\]]+\]:`) and add a footnote case to test_reference_style_links, so the test fails if footnotes get flagged again. Blocking because the regex change needs a second look against the other reference-definition forms.

## Notes

grade.py accepts metadata with no `prompt` key because of `meta.get("prompt", spec["prompt"])`. That matches the plan, which joins on eval_id alone, so I raise no finding.
