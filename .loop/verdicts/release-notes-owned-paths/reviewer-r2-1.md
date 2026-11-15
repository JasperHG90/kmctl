---
type: verdict
title: 'Verdict: release-notes-owned-paths reviewer round 2'
description: 'reviewer verdict for round 2 of release-notes-owned-paths: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T06:47:39+00:00'
slug: release-notes-owned-paths
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is resolved. The command now reads all of stdin before it decides, so the
writer in release-tag's pipeline is never cut off, and a new test pins this
under pipefail. Nothing else in the touched code regressed, and the gates
are green.

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests, integration and
  rows r1, r2, r3 all pass; stamp green
  803217b0dd146bb41b4c76c92e33623a9315c53f9ef18231eb0c7b2b49494d9e.
- Read scripts/release_paths.py: `main` reads `sys.stdin.read().splitlines()`
  into a list, then applies `owns`; exit codes 0/1/2 match the docstring.
- Reproduced the round 1 case against the new script: with
  `set -euo pipefail`, one docs path followed by 20000 kmaudit paths piped
  into `release_paths.py kmctl` takes the "owned" branch (it took "not" with
  exit 141 in round 1). A kmaudit plus .okf input to kmctl still exits 1.
- Read the new test
  test_the_command_reads_every_path_so_the_writer_never_dies_of_sigpipe: it
  runs the real script through `cat | python` under `set -euo pipefail` with
  about 500 KB of input, well past the pipe buffer, and asserts the `if`
  takes the owned branch. Against the round 1 code the `cat` would die of
  SIGPIPE and the assertion would fail, so it covers the regression.
- release-tag.yml's loop still pipes `git diff --name-only` into the script
  unchanged.

## Findings

- f1: resolved in scripts/release_paths.py:47-50, which drains stdin before
  deciding, and covered by the new pipefail test in
  tests/scripts/test_release_paths.py.
