---
type: verdict
title: 'Verdict: new-doc-verb reviewer round 2'
description: 'reviewer verdict for round 2 of new-doc-verb: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:10:05+00:00'
slug: new-doc-verb
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both findings sent back are fixed and the fixes broke nothing I could find. The shared `one_line` and `link_text` helpers keep index entries on one line for both verbs, and one `next_step()` builds every Next line, each ending in `kmctl check`. Pass.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1 to r4 pass, "stamp green: c25c415f2d96bdcf4fff71e951d788d1e91771149ab89b645045b348c94c365b". That fingerprint matches the round's placeholder.
- Read the staged changes to src/kmctl/concepts.py, src/kmctl/docs.py, src/kmctl/__init__.py and tests/test_new_doc.py. docs.py imports `link_text` and `one_line` and no longer has its own copy. `new_concept` collapses the title before it writes the front matter, the heading and the entry. `new_doc` collapses the title and the description.
- The two new tests each give a title with a line break and then run `kmctl check` (exit 0). The doc test also asserts the exact one-line entry. The older concept test for a multi-line description still passes.
- Ran it by hand in a scratch repo: a title of `  [A]\n\tb  ` with a two-line description gives `- [(A) b](how-to/a-b.md): x y`. A whitespace-only title is refused with exit 1 and nothing written. `kmctl new decision $'Use\na [queue]'` writes a one-line title and the entry `(queue)`. `kmctl check` passes on the result.
- Next lines: grep finds no other `Next:` string in src/. init, the five concept verbs, `new doc` and `decision supersede` all go through `next_step()`. No test, doc or skill quotes the old strings.

## Findings

- f1: resolved in src/kmctl/concepts.py (`one_line`, `link_text`) and applied in `new_concept` and src/kmctl/docs.py `new_doc`. Tests for both verbs are in tests/test_new_doc.py.
- f2: resolved. TYPES in tests/test_new_doc.py lists every skeleton heading per type and r1 asserts all of them.
- f3: resolved. `next_step()` in src/kmctl/__init__.py builds every Next line, and each one ends with `kmctl check`.

## Notes

init's Next line no longer says to commit docs/ and .okf/, and supersede's no longer says to commit both records. The rule asks for a kmctl step, so I don't count this as a defect.
