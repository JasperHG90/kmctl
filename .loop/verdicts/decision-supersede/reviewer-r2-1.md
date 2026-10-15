---
type: verdict
title: 'Verdict: decision-supersede reviewer round 2'
description: 'reviewer verdict for round 2 of decision-supersede: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:57:41+00:00'
slug: decision-supersede
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All five round-1 findings are fixed, and the fixes broke nothing I could find. On this repository's own wrapped index, the note now lands after the entry's last line. The verdict is pass.

## Checked

- Ran `loopctl gate stamp` from the worktree. Lint, format, tests and eval rows r1 to r5 all pass: "stamp green: 9f365c768718d01f98073c308c372b3bc82c24fe947200994b1e42e89167c923".
- Read supersede.py and test_supersede.py in full, plus the decision group in `__init__.py`.
- Ran `decision supersede 3 --by 9` on a copy of this repository's `.okf/`. The diff shows status deprecated, the body unchanged with a dated Correction appended, the back-link on 0009, the log line, and the index line 8 now ends "...depends on okf@scaccogatto. (superseded by ADR 0009)". `kmctl check` passes. A second run refuses with exit 1 and a next step. `supersede ² --by 9` refuses with exit 1 and no traceback.
- `kmctl decision --help` names the prerequisites (kmctl init, kmctl new decision).

## Findings

- f1 resolved: `_entry_end` (supersede.py:41) extends the entry to a blank line or the next list item, and `test_supersede_note_goes_after_a_wrapped_entry` covers it. Confirmed on the real index.
- f2 resolved: test_supersede_links_both_ways matches `^## Correction, \d{4}-\d{2}-\d{2}$`.
- f3 resolved: test_supersede_refusals checks exit 1 and `refused:` on stderr for missing old, missing new, already deprecated, same id and a non-ASCII digit, and checks that no file changed. A separate test covers the missing index entry.
- f4 resolved: `_number` uses `re.fullmatch(r"[0-9]+", ...)`.
- f5 resolved: the group help names its prerequisites. The self, already-deprecated and missing-entry refusals each give a next step.

## Notes

`_entry_end` would also treat a heading line placed straight after an entry, with no blank line between, as part of that entry. Neither the index that `kmctl new` writes nor this repository's index has that layout, so I am not raising it as a finding.
