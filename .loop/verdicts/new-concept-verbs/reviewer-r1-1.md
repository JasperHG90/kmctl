---
type: verdict
title: 'Verdict: new-concept-verbs reviewer round 1'
description: 'reviewer verdict for round 1 of new-concept-verbs: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:48:20+00:00'
slug: new-concept-verbs
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The verb works for ordinary titles. It numbers decisions, creates sections, indexes and logs each concept, and refuses existing files without writing anything. Run on a copy of this repo's bundle, it wrote ADR 0010 and kmctl check still passed. One blocking bug remains: a title with square brackets produces an index entry the index check cannot read, so the bundle fails kmctl check straight after kmctl new.

## Checked

- Ran `loopctl gate stamp` in the worktree: lint, format, tests and rows r1 to r5 all pass, stamp green fbab73995779886681743723774a2e82fa3630a5d450c18866c4c3b0077e9a21.
- Read src/kmctl/concepts.py, the new command in src/kmctl/__init__.py and tests/test_new_concept.py in full, along with checks.py, okf.py, handoffs.py, conftest.py, the manifesto (I4) and .claude/rules/okf-bundle.md.
- Rows. r2 asserts 0007 is followed by 0008 and that stale_after is set. r3 asserts the section index and the root link exist. r4 asserts the entries, the log ids, kmctl check exit 0 and the strict vendored validator exit 0. r5 asserts a non-zero exit and that no .md file changed. r1 is weaker (f4).
- Probes in scratch repos: a decision on a copy of the real .okf/ (wrote 0010, check passed, log line under the existing date heading); a practice titled 'Use [WIP] flags' (check fails, f1); a handoff titled 'Café état' (named caf-tat, f2; validator conformant, kmctl handoffs lists it); a two-line description (f3); a missing .okf/index.md (refused, exit 1).
- Consistency: the front matter fields fit I4. Decisions match the repo's 'ADR NNNN:' titles. The log format matches .okf/log.md. The help text names every parameter.

## Findings

- f1: the index entry is `- [{title}]({rel}): ...`. The `_ENTRY` regex in checks.py wants `\[[^\]]*\]\(`, so a title like 'Use [WIP] flags' produces a line that is not an entry, and the new file is reported as "not listed". Escaping the brackets with a backslash does not help, because that regex still stops at the first `]`. The fix has to agree with checks.py (refuse brackets, strip or replace them in the link text, or change the regex), so it should come back for review. Add a test for it.
- f2: `re.sub(r"[^a-z0-9]+", ...)` on the lowered title throws away accented letters. Folding with `unicodedata.normalize("NFKD", ...)` before the substitution is a plain fix. Non-blocking: the file is still valid and indexed, only badly named.
- f3: the CLI says "One sentence", but nothing stops a newline. The YAML side is safe because json.dumps escapes it, but the index line breaks. Refusing a description with a newline (or folding it to spaces) is a plain fix. Non-blocking because it needs a deliberate odd input.
- f4: row r1's fails_when includes "misnamed". Asserting the expected path for every kind, and the title in the front matter, would close that gap. Non-blocking: a test-strength fix I trust without a second look.
