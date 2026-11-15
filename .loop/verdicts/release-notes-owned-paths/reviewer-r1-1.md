---
type: verdict
title: 'Verdict: release-notes-owned-paths reviewer round 1'
description: 'reviewer verdict for round 1 of release-notes-owned-paths: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:50:19+00:00'
slug: release-notes-owned-paths
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The rule moved into scripts/release_paths.py cleanly, release_notes.py and
release-tag both use it, the bookkeeping paths are excluded for both packages,
and ADR 0012 and the docstrings agree with the code. All gates and rows are
green. One regression blocks: the new command short-circuits on stdin, which
under the step's `pipefail` makes release-tag miss a late commit it owns once
that commit's path list is bigger than the pipe buffer.

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests, integration and
  rows r1, r2, r3 all pass; stamp green
  6338d4810d893969149e25d845e9ef5a9666846cb76c446fda8b01b736d86854.
- Read the full uncommitted diff (release-tag.yml, ADR 0012, summary.md,
  release_notes.py, both test files) and the new release_paths.py and
  test_release_paths.py in full.
- r1: test_owns covers each bookkeeping path for both packages, shipped paths
  for their owners, and packages/other; the command tests cover 0/1 exit for
  the plan's path sets and 2 for an unknown package. Asserts the row's
  fails_when.
- r2: the new release_notes test drafts both packages over a bookkeeping-only,
  a bookkeeping+kmaudit and a .claude+docs commit and asserts each is in only
  its owner's notes. Asserts the row.
- r3: the late-step test copies this tree's release_paths.py into the temp
  repo and runs the real step for both packages; a late .okf+uv.lock commit is
  not named, the shipped late commit is. The static test checks the step names
  release_paths.py, has no awk in the loop and no packages/kmaudit literal;
  test_release_tag_never_writes_its_own_notes still stands. Asserts the row.
- Checked that .claude/ ships in no package: kmctl's APM package lives in apm/,
  and apm.yml installs .claude/ content from another repository.
- Grepped for other copies of the rule outside .loop/: none left.
- Reproduced f1: with `set -o pipefail`, piping one docs path followed by
  20000 kmaudit paths into `python3 scripts/release_paths.py kmctl` gives
  PIPESTATUS `141 0` and the `if` takes the "not named" branch.

## Findings

- f1: `main` returns `any(owns(...) for p in sys.stdin ...)`, which stops
  reading at the first owned path and exits. The writer, `git diff
  --name-only`, is still blocked on a full pipe for any commit whose path
  list passes about 64 KB (roughly 1500 paths), gets SIGPIPE, and exits 141.
  The step runs `set -euo pipefail`, so the pipeline's status is 141, the `if`
  is false, and the commit is dropped from the warning with no error. The awk
  this replaces used an END block, so it always drained stdin; the step's
  comment on drafted_from names this same hazard. Fix: read all of stdin
  before deciding (for example `paths = sys.stdin.read().splitlines()`), and
  add a test that pipes a large path list with an early owned path through
  the command under `set -o pipefail` and checks the pipeline succeeds.
