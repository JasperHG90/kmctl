---
type: verdict
title: 'Verdict: first-decision-detect reviewer round 1'
description: 'reviewer verdict for round 1 of first-decision-detect: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:17:27+00:00'
slug: first-decision-detect
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. `_write_first_decision` returns when any `*.md` other than `index.md` sits anywhere under `.okf/decisions/`, without reading front matter, and `_has_first_decision` and the unused `okf` import are gone. A fresh bundle still gets `0001`. The docs, epilog, docstrings and ADR 0011's Correction all state the new rule. One test-strength finding, which does not block: two of the new tests do not assert the exit code.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and rows r1 to r4 all pass, "stamp green: 76ecb1622b263d0de40fbcac7150f6de87a279c7498adbce226ea1a70e3438a3".
- I read the full uncommitted diff against HEAD on `loop/first-decision-detect`: eight files.
- `Path.rglob` on a missing `decisions/` yields nothing, so a fresh repo still falls through to the write. The UTF-8 guard and the updated/created bookkeeping after it are unchanged.
- I put the new tests on top of the old `scaffold.py` in a scratch copy. r1, r3 and the subfolder test fail there, and r2 passes, as it should, because it guards the fresh-bundle path that did not change. So r1 and r3 assert their `fails_when`. r1 snapshots every file under `.okf/` with bytes and mtime, and checks exit code 0.
- r4: all 60 tests in `tests/test_init.py` pass. The three tests that copied this repo's bundle now empty its records through `_copy_bundle_without_decisions`, so they still test writing into a kept bundle.
- r5 (judgment): ADR 0011 has a "Correction, 2026-10-19" that states the empty-folder rule, cites issue #26 and names the rejected tag. The `ScaffoldResult` and `scaffold()` docstrings, `_write_first_decision`'s new docstring, the `kmctl init` epilog and `docs/reference/commands.md` all state the new rule. A grep for "that title" outside `.loop/` finds only ADR 0011's original Decision text, which the Correction amends. The manifesto line (ADR 0011, "a first decision") never stated the title rule, so it correctly stays unchanged. The decisions index note, the log line and the summary ack (checked.against moved to 0011) are consistent. r5 holds.
- The subfolder extension goes beyond the plan's wording, but it follows the plan's intent (a moved decision log counts), and the ADR and the docs say so.

## Findings

- f1 (test-strength, not blocking): `test_init_counts_unparseable_record` and `test_init_counts_records_in_subfolders` assert only that no record was written. Add `assert result.exit_code == 0, result.output`, as r1 does, so a crash cannot pass for "nothing written".

## Notes

The `ScaffoldResult` docstring now has one line ("when it writes a manifesto or summary into a kept bundle it adds its root index entry and") much longer than the lines around it. Ruff accepts it. You could rewrap it while fixing f1.
