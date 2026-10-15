---
type: verdict
title: 'Verdict: new-doc-verb reviewer round 1'
description: 'reviewer verdict for round 1 of new-doc-verb: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:07:19+00:00'
slug: new-doc-verb
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The verb does what the plan asks. Each type lands in its folder with its title and skeleton, the index entry is in the format kmctl check reads, both refusals write nothing, and the old `kmctl new KIND TITLE --description` calls still work. No finding blocks. One edge-case bug (f1), one weak test (f2) and one rule departure carried over from the existing verb (f3) each need a plain fix, so the label is fix.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1 to r4 pass, "stamp green: b1adc436e2b4d7d64b86bab91351ce9256833c6a6392c7d4115f0035e2daa49a".
- Read the staged diff in full: src/kmctl/docs.py, the `new` group, the concept-verb factory and the `doc` command in src/kmctl/__init__.py, the briefing line, and tests/test_new_doc.py. tests/test_help.py walks the groups, so it covers every `new` leaf.
- Rows: r1 checks the folder, the title line and one heading per type (see f2). r2 asserts the README link and that `kmctl check` exits 0. r3 asserts exit 1, "kmctl init" on stderr and no docs/ folder. r4 asserts exit 1 and that the page is unchanged.
- Ran it by hand on a scratch repo (in the scratchpad, not the worktree): brackets in the title and a multi-line description give a valid entry and check passes. `--json` prints path and created_folder. An unknown type exits 2 and names the four legal values. A title with no letters is refused. `kmctl new decision` without --description still asks for it. `kmctl new --help` lists all six verbs and names kmctl init.
- Consistency: the briefing routing, src/kmctl/rules/docs-layout.md and the folder names agree (tutorials/, how-to/, reference/, explanation/). There is no docs/ in this repo for the change to update.

## Findings

- f1: `kmctl new doc how-to $'Two\nlines'` exits 0 and writes `- [Two` and `lines](how-to/two-lines.md)` on two lines. The checker reads entries line by line, so `kmctl check` then fails with "not listed in docs/README.md". `kmctl new decision` does the same today (pre-existing, but the rules say to fix it when found). Fix: collapse whitespace in the link text, or refuse a title with a line break, in one shared helper. docs.py also re-implements `concepts._link_text` inline, so the helper should be shared. Add a test that runs kmctl check after a multi-line title. Not blocking: the fix is small and a test proves it.
- f2: TYPES in the test holds one heading per type. The row's fails_when says "lacks the title or skeleton headings". Assert every heading in `docs.SKELETONS[kind]` (or a literal list). Not blocking: it only makes the test stronger.
- f3: cli-interface.md asks for one `Next: kmctl ...` line built by one shared function. `new doc` copies the concept verb's hand-written "Next: write the sections of ..." string. Build the line in one helper and name a kmctl step when one follows (for example `kmctl check` before commit). Not blocking: a wording and refactor fix.
