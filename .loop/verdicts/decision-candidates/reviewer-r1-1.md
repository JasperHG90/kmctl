---
type: verdict
title: 'Verdict: decision-candidates reviewer round 1'
description: 'reviewer verdict for round 1 of decision-candidates: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T16:23:19+00:00'
slug: decision-candidates
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The split is right: on 14799749..ee87e883 the verb gives the same 161 changes as the prototype's units, and the walk copies `release_notes._first_parent` line for line. The tests check each row's fails_when. The default start, though, breaks on two common paths. It reads `.okf/decisions/` from the working tree under `--path` and asks git when that file was added. A record that is not committed yet, or a run from a subdirectory, gets None, and the verb lists the whole history with no warning. That is f1, and it blocks. The words signal also misses phrases split by line wrapping (f2, not blocking).

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2 and r3 all pass, `stamp green: 99d56318c21603d27ceb6fa08b8ba6a942ba6d50b0cbea0b57a3c680abb738d1`. `kmctl check`: all checks passed.
- Read candidates.py, the CLI diff, test_candidates.py, the docs section, ADR 0047, and the index, log, summary and prototype edits in full.
- I ran the verb over 14799749..ee87e883 by patching the top-level tip, and compared it with `results/signals.jsonl`. The sha sets are the same (161). Six changes differ, all in `words`. Five are True where the prototype said False, because the verb does not strip decision sentences. That is the right call for live use. One (bc6f0ebe) is False where the prototype said True: f2.
- Walk edge cases. A pull request that carries tickets lists its tickets and inner commits, and the pull request itself drops out. A pull request with no tickets stays one change. A sync is read through and the sync merge is skipped. A root commit goes through diff-tree --root. A `--since` that is not an ancestor works as `HEAD ^since`. A release pull request is skipped.
- Reproduced f1. In this worktree, where 0047 is staged but not committed, `kmctl decision candidates` lists 165 changes, against 2 on main. From `packages/kmctl` it also lists 165. `default_since` returns None in both cases. In a scratch repository, `--path repo/sub` lists Start and Before ADR, which come before the record.
- Eval rows. r1's tests check the exact set of subjects, the default start, `--since` and the no-record case. r2's tests check every field, `recorded` for an added and an amended record, the score order (the fixture's natural order is not sorted, so dropping the sort would fail), the table and that status and refs do not change. r3's tests check both refusals (exit 1, one stderr line, the fix), the reference section and 0047's schema. The help tests pass.
- ADR 0047's numbers match the prototype README: 25 of 30, 10 of 17 (59%), $3.19, 161 changes, and 5 of 30 lost at score 2. The archived plan path `.loop/archive/SLUG/plans/SLUG/README.md` matches the real archive layout. The prototype's hide.py looks in the wrong place there.

## Findings

- f1: `default_since` globs `root/.okf/decisions/*.md` in the working tree, while its docstring says "in HEAD". It then runs `git log --diff-filter=A -- path`, which finds nothing for a record that is not committed. With `--path` (default `.`) set to a subdirectory, it finds no records at all. Either way the default falls back to the whole history without a word. The first case is likely right after `kmctl new decision`. The second is likely when someone runs kmctl from a package folder, as here, where the result was 165 changes instead of 2. `_plan` and `_intent` also read `root/.loop`, so from a subdirectory they miss every plan. Fix: resolve the top level with `git rev-parse --show-toplevel`, take the newest record from HEAD's tree (`git ls-tree --name-only HEAD .okf/decisions/`), and read plans from the top level. Add r1 tests for a record that is not committed and for a run from a subdirectory. The current default-start test only covers a record committed at the root.
- f2: `_WORDS` uses literal spaces inside its phrases, and `text` keeps the body's newlines. On bc6f0ebe, "instead\nof" is missed, where the prototype's `strip()` folded whitespace and matched it. Fix: collapse whitespace first (`" ".join(text.split())`), or use `\s+` in the phrases, and add a test with a wrapped phrase.

## Notes

- Commits usually add a record inside a ticket branch, so the default start is that inner commit. The ticket merge that brought the record in is then listed (with `recorded`), and so is any main commit made while the branch was open. That is harmless and arguably useful, but the help's "after the commit that added the newest decision record" reads as if that merge would not be listed.
- An empty repository fails with git's own error ("does not have any commits yet"), passed through as a refusal with no fix line.
