---
type: verdict
title: 'Verdict: docs-frontmatter-indexes reviewer round 1'
description: 'reviewer verdict for round 1 of docs-frontmatter-indexes: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T17:09:11+00:00'
slug: docs-frontmatter-indexes
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. Generated folder indexes with a marker,
`kmctl check --fix`, the error for a missing or stale folder index, the
warning level for a root index with no folder link, hand-written indexes
left alone with a warning, optional OKF fields on docs pages with shape
checks, docs pages in `review due` (also without `.okf/`), the
`.pre-commit-hooks.yaml` hook and the migrated docs/ all work. I re-ran
the gates and they are green. Three findings, none blocking: a leftover
false sentence in this repo's docs-layout rule, an r7 test whose "absent
front matter" case has no absent front matter, and a tutorial version
claim the new output makes false.

## Checked

- Gates: `loopctl gate stamp` from the worktree gave "stamp green:
  d541da4729b6c4e7c085b95168d74ebf029ec6668d5f31ff5d849625bd985578". lint,
  format, tests and integration passed, and so did every row r1-r9, r11-r13.
- Code read in full: `src/kmctl/docs_index.py`, plus the diffs to `checks.py`,
  `docs.py`, `scaffold.py`, `review_due.py`, `kinds.py`, `briefing.py` and
  `__init__.py`. I checked the paths that could go wrong. `missing_ok`
  stops a second error when the root links a missing folder index.
  `is_generated` handles non-UTF-8 and empty files. A hand-written index
  is never written by `fix_folder_indexes`, `new_doc` or `scaffold`.
  `--fix` prints its "fixed" lines to stderr under `--json`. A docs page's
  baseline is its latest `verified` date or, with none, its last commit.
  `_resolve` is called with okf=root, so a leading `/` means the repo root.
- Ran it by hand in a scratch repo: init, add an unindexed how-to,
  `check` (1 error, 1 warning, exit 1), `check --fix` (writes the index,
  passes with 1 warning), add the root link (clean), then `new doc` with a
  description holding `:` and `[ ]`. The YAML is quoted, the index entry
  is right and the root link was added. The output matches the tutorial
  text.
- Rows. r1: the snapshot diff proves nothing else changes, and the
  second run is idempotent. r2: one error for each folder case, the fix
  names `--fix`, and the out-of-folder pages are errors. r3: check and
  action test (exit 0, the warning shows in the summary). r4: all three
  writers leave the file unchanged, and check warns with exit 0. r5:
  fields, no `verified`, the folder index, update creates indexes and
  leaves the root index alone. r6: stale, source changed after the
  page's commit and after `verified`, no `.okf/`, the docs/ id prefix and
  the `--json` keys. r7: see f2. r8, r9, r11 (offline shape plus a real
  prek run from a scratch repo pinned to a commit of a copy), r12, r13:
  each asserts its fails_when.
- r10 (judgment): ADR 0022 says in plain words why docs/ is not a bundle.
  Diataxis sorts by what the reader wants to do, OKF by kind of
  knowledge, users would see YAML they never asked for, and the split is
  by reader. Folder indexes are generated because "a script can write it,
  so a script does". The root stays hand-written because it "is where a
  person explains the docs". The reasoning matches the plan. The rules,
  the commands reference and the tutorial agree with it. Pass.
- Consistency: the manifesto I4 and its kmctl description, the
  architecture overview, the commands reference, the shipped rules, the
  CLAUDE.md block, the briefing, the write-docs, audit and auditor
  prompts and the kinds schema all agree with the code, except f1 and f3.

## Findings

- f1: `.claude/rules/docs-layout.md` lines 10-13 kept "lists every page"
  and added the new sentence after it, so the rule contradicts itself.
  Delete the old sentence, as the two shipped copies already do.
- f2: r7's command never checks a page with no front matter. Give
  `test_field_shape_good_and_absent_pass` one page with no front matter
  (for example, leave `_docs`' upgrade.md alone and write the good front
  matter to a third page).
- f3: the tutorial's "run ... with kmctl 0.1.0" claim no longer holds for
  the new check / check --fix output. Say which version printed it.

## Notes

README.md and the how-to pin `rev: v0.3.0` for the new hook. That tag
does not have `.pre-commit-hooks.yaml`. It follows the repo's habit of
bumping every pin at release, so I did not raise it as a finding. Check
it at release time.
