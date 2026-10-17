---
type: verdict
title: 'Verdict: ci-toiminnot reviewer round 1'
description: 'reviewer verdict for round 1 of ci-toiminnot: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:13:46+00:00'
slug: ci-toiminnot
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. ci.yml's prek job puts uv on PATH (cache off) and then runs toiminnot's pre_commit action, which runs prek, at the justfile's prek version on Python 3.12. The tests job runs toiminnot's pytest action on tests/ with markers "not integration" on Python 3.12. Both are pinned to the v1.3.0 SHA, and the knowledge job is unchanged. test_ci.py checks each eval row, and the stamp is green.

## Checked

- Read the full diff and both changed files. Fetched actions/pre_commit and actions/pytest at 4763b907 and confirmed their inputs (prek_version, python_version, directory, markers), that each checks out the repo itself, that pre_commit installs no uv, and that the pytest action's empty markers default becomes -m "". The ci.yml comments match what the actions do.
- Risk the spikes did not cover: the pytest action pins uv 0.7.x, but uv.lock is revision 5 and spike 2 used uv 0.13. In a scratch clone, uv 0.7.22 ran `uv sync --all-extras --all-groups` without touching the lock, and `uv run pytest tests -m "not integration"` with uv 0.7.22 on PATH gave 710 passed, 8 deselected.
- The pre_commit action creates a venv/ directory in the workspace. The hooks run only on docs/, .okf/ and README.md and file lists come from git ls-files, so the directory has no effect.
- Eval rows: in a scratch clone I changed markers to "", prek_version to 0.5.4 and the toiminnot pin to @v1.3.0. The r1, r2 and r3 tests each failed, so they assert their fails_when. The -k filters select the right tests. r4's tests are unchanged.
- Consistency: the how-to cites ci.yml only for its knowledge job, which is unchanged, and the test module docstring still holds.
- `loopctl gate stamp` run by me: lint, format, tests, integration and eval rows r1 to r4 all pass. Result: "stamp green: af6dc839e6ee9fb7556b1c82a6c155f7375ddfb2015f6ba09f3a24df56a969aa".

## Findings

None.
