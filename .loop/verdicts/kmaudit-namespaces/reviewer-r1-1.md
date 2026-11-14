---
type: verdict
title: 'Verdict: kmaudit-namespaces reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-namespaces: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T13:47:15+00:00'
slug: kmaudit-namespaces
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The core works. Each folder gets its own store, paths narrow to the owning
namespace, checks leave out the audited folder, the page and coverage work for
a plain folder, and the legacy store copies across with no loss. I re-ran the
real-data check and it matches the author's claim. Two correctness bugs block
the change. In a repository root without .okf/, the default path makes a
whole-repo '.' namespace that swallows every later folder (f1). Concurrent
first opens of a legacy store fail with disk I/O errors (f2). Two eval-row tests
should be stronger (f3, f4).

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and integration
  all pass, and rows r1 to r9 pass. "stamp green:
  4f5a1f3f7021085022a1e35d0ae24be22c37507eb70f27a963a8ecdf09d6c14f".
- Read the full staged diff against agent-audit: namespaces.py,
  sections.resolve_target and concept_paths, store.py (copy, meta step),
  steps.Repository, every Store and Repository call site in verbs.py,
  check_verbs.py, ui.py, coverage.py and cli.py, ui.html, the instructions
  comment, the agents and skills, the README, commands.md, the .okf
  architecture pages, the ADR 0043 amendment, and the log.
- Eval rows: opened each test the row commands select. r2 (apart, plus the
  refused-submit test), r3, r4, r5, r6, r7, r8 and r9 assert their fails_when.
  r2b and r1 are weaker than their rows (f3, f4).
- Real data: extracted .okf/ at 9dcbb0bd into a fresh git repo, copied the
  operator's .kmctl/audit.sqlite, and ran `kmaudit claims todo --json`. It
  gave namespace .okf, 207 up to date, 0 pending and 0 sections handed out.
  The legacy file's md5 was unchanged. `kmaudit namespaces` listed 207
  sections, 1281 claims and 790 checks (kind = 'check').
- f1: made a scratch repo with docs/, handbook/ and README.md and no .okf/.
  `kmaudit claims todo --json` returned namespace '.', took sections from all
  three, and wrote .kmaudit/..sqlite. After that, `kmaudit claims todo docs`
  returned namespace '.' with next `--path .`.
- f2: ran six parallel `kmaudit claims list .okf` over a fresh legacy store,
  five times. Each trial had 5 of 6 processes refused with "disk I/O error".
  The store that survived passed integrity_check.

## Findings

- f1 (bug, blocking): the case `path == root` without .okf/ falls through to
  "open a new folder namespace" with the root as its folder. The skills say
  the default path "means .okf", which is only true when .okf/ exists. A
  whole-repo namespace also audits every .md in the repository (.loop/,
  .claude/, vendored READMEs), and Repository(root, root) leaves nothing out.
  Refusing the root when it holds no .okf/, with a message naming a folder,
  would match both the old behaviour and "every folder its own namespace".
  Add a test for it.
- f2 (bug, blocking): `_copy` uses one fixed `.partial` name and an
  unconditional `replace`. The check that the target does not exist yet and
  the rename are not atomic together, so a second copier can rename over a
  store another process has already opened and migrated. Its -wal and -shm
  then pair with a different file, which is how the I/O errors appear, and
  writes already made can be lost. The fix needs a unique partial name and a
  publish step that does not overwrite (os.link, or a lock held across the
  check, copy and open), plus a concurrent test. A wrong fix here ships data
  loss, so I want to see it again.
- f3 (test-strength): widen r2b's -k to also select the refusal test (and the
  page-with-no-namespace test if wanted), or rename the tests so "maps"
  matches them.
- f4 (test-strength): assert the full set of section ids (for example
  guide#output and guide#start), not just the concepts.

## Notes

- namespaces.repository_root falls back to the path itself outside git, but
  resolve_target falls back to the folder's parent. Outside git,
  `kmaudit namespaces docs` and `kmaudit claims todo docs` therefore look in
  different .kmaudit/ folders. The help says kmaudit needs a git repository,
  so I am not filing it.
- The plan said 1137 checks; the listing shows 790 because it counts only
  kind = 'check', which leaves out reasons. The CLI help and the Namespace
  docstring both say so.
