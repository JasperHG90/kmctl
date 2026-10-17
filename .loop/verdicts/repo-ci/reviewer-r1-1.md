---
type: verdict
title: 'Verdict: repo-ci reviewer round 1'
description: 'reviewer verdict for round 1 of repo-ci: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T17:45:46+00:00'
slug: repo-ci
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. ci.yml runs on every pull request and every push to main, with three jobs: knowledge (`uses: ./` after a full-history checkout), prek (`uvx prek@0.5.5 run --all-files`, the version the justfile pins) and tests (`uv run pytest`, the default tier). Actions are pinned by SHA with version comments that match release-tag.yml, and setup-uv runs with its cache off. knowledge.yml is deleted, and the how-to now cites ci.yml's knowledge job. One wording slip in the how-to remains (f1). It does not block.

## Checked

- Read the diff in full: the staged deletion of knowledge.yml, the unstaged how-to edit, and the untracked ci.yml and tests/test_ci.py.
- `loopctl gate stamp` from the worktree: lint, format, tests and integration pass, rows r1 to r7 pass, "stamp green: b906426ff5ba39ed32b3f9e8a38010f620038eddd8a233e7985e25f0107cfeaf".
- `uvx prek@0.5.5 run --all-files` passes and leaves the tree unchanged. `kmctl check` on the worktree prints "all checks passed".
- Eval rows, test by test. r1 asserts `pull_request` in `on` and `push.branches == ["main"]`. r2 finds the job whose steps contain `{uses: ./}` and asserts that its checkout has `fetch-depth: 0`. A missing key raises, which fails the test. r3 reads the version from the justfile and asserts the exact run line. r4 asserts that the only pytest run line is exactly `uv run pytest`, so adding `-m` fails it. r5 asserts that every non-local `uses` is owner/repo@40-hex and that every setup-uv step has `enable-cache` set to False. r6 asserts that knowledge.yml is absent. r7 extracts the "quoted from" note and the step 4 "This is ..." sentence and checks that every `.github/workflows/` path in them exists. I ran its regexes by hand: the step 4 capture ends at "`uses" but still contains the ci.yml path, so changing that sentence back to knowledge.yml would fail the row. Each `-k` selector picks at least one test, because pytest exits 5 when it selects none.
- Consistency: the pyproject marker description says the integration gate in .loop/config.toml runs the integration tier, which matches the comment on the tests job. grep outside .loop/ finds no other reference to knowledge.yml besides the how-to's instruction to create one in the user's own repo, which the plan keeps as is.

## Findings

- f1: the step 4 sentence says checkout is "at its version tag", but the quoted block uses @v4 while ci.yml pins v7.0.1. The fix is a wording change, so it does not need another round.

## Notes

prek's `--all-files` covers tracked files only, so it did not check ci.yml and tests/test_ci.py while they are untracked. The ruff gates cover the test file, and the YAML parses in the tests.
