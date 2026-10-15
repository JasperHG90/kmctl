---
type: verdict
title: 'Verdict: decision-supersede reviewer round 1'
description: 'reviewer verdict for round 1 of decision-supersede: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:55:14+00:00'
slug: decision-supersede
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The verb does what the plan says on a bundle written by `kmctl new`, and the gates and the strict validator pass. It breaks this repository's own decisions index, though: every entry there wraps over two lines, and the marker lands mid-sentence (f1). That blocks. The other findings are test strength, hardening and help wording. A plain fix will do for each.

## Checked

- Ran `loopctl gate stamp` from the worktree. Every gate passed, as did eval rows r1 to r5: "stamp green: 3e7413269acc681a5ad93709355a14c66d9e4ffe4a90e83726625233d2c7c6b5". The change is staged, not committed, so I read `git diff HEAD`.
- Read supersede.py, the CLI diff, the concepts.py rename and test_supersede.py in full. I also read okf-bundle.md, cli-interface.md, the manifesto's Parts section and test_help.py. test_help.py walks nested groups, so the new verb is covered.
- Ran the verb on a copy of this repository's `.okf/` (`supersede 3 --by 9`). Old status became deprecated and decision_status stayed as it was. The body was unchanged with a dated Correction appended. The new record got its back-link and the log line names both ids. `kmctl check` and the pinned strict validator both pass. The index line came out as "...: The Claude Code (superseded by ADR 0009)\n  plugin comes first...", which is f1. Running it a second time refused with exit 1.
- Ran `supersede ² --by 9`: it fails with a ValueError traceback (f4).
- Eval rows: r1 checks status, decision_status and the body prefix. r3 finds the line by its link and checks the marker. r4 checks the log's last line and runs the strict validator. r2 and r5 are weaker than their fails_when (f2, f3).

## Findings

- f1 (bug, blocking): `lines[hits[0]] += ...` appends to the line that holds the link. Index entries may continue on indented lines, as this repository's own `.okf/decisions/index.md` does. Put the marker at the end of the entry, meaning the last line before the next `- ` item or a blank line. Add a test with a wrapped entry.
- f2 (test-strength, not blocking): assert that the heading matches `## Correction, \d{4}-\d{2}-\d{2}`, or the date from a fixed `now`. A plain fix is enough.
- f3 (test-strength, not blocking): assert that `refused:` appears in the stderr of each case and that there is no traceback. Add the same-id and missing-index-entry cases. The behaviour is already right, so this only makes the test stronger.
- f4 (hardening, not blocking): use `value.isascii() and value.isdigit()`, or a regex, so bad input gets the normal refusal.
- f5 (design, not blocking): add the prerequisites to the group help. Give each refusal a next step where one exists. Already deprecated: "nothing to do". Same id: give two different numbers. Missing entry: add the entry to the index by hand.

## Notes

No verb uses a shared function for its `Next:` line, which cli-interface.md asks for. That was true before this ticket and is out of scope here.
