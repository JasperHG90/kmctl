---
type: verdict
title: 'Verdict: release-notes-hermes reviewer round 1'
description: 'reviewer verdict for round 1 of release-notes-hermes: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T22:10:32+00:00'
slug: release-notes-hermes
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. Untrusted text never reaches a shell, a failed or timed-out Hermes step always falls back to the draft, and the checks match the plan's list. One small bug remains: a response file that is not UTF-8 crashes the script and fails the job (f1). The fix is plain, so it does not need to come back. f2 is optional hardening.

## Checked

- Ran `loopctl gate stamp` in the worktree myself. Lint, format, tests, integration and eval rows r1 and r2 all passed: "stamp green: ef295b15...".
- Injection: no `${{ }}` in any run script in release.yml, and test_hermes_release_runs_never_expand_an_expression pins that for every job. TAG and RESPONSE_FILE come in through env. The draft reaches Hermes only as a file path in `with:`.
- `user_message: '@path'` is the same form hermes-issue-triage.yaml uses at the same SHA. The prompt file is byte-identical to spike 3's.
- Fallback: continue-on-error with timeout-minutes 10. spike2.py notes that the action sets response_file only when the runner exits 0, so a failed step gives an empty RESPONSE_FILE, which the script treats as `missing` and tests cover. The script's stdout goes to a temp file and replaces TAG.md only after the script succeeds, so TAG.md can never be left missing or empty.
- Checks against the plan: cleaning (comments and trailers, preamble, wrapping fence), the empty check, headings in order, the tail after What changed with trailing whitespace ignored, the reference set (added and dropped) and a reference on every bullet. The draft starts at `## What changed`, so "everything after What changed" is the same as the plan's "from Other changes to the end".
- Eval rows: test_hermes_release_notes.py runs one case per check and asserts the draft comes back byte for byte, the warning names the check, the before file is removed, and the exit code is 0. The r2 tests pin the SHA (equal to triage's), secret, model, prompt, the full toolset set, max_iterations, continue-on-error and the timeout. They also run the check, summary and bump steps in bash, assert the PR body carries the before block, and assert the before file is not committed.
- ADR 0035 and the release.yml header comments agree with the code.

## Findings

- f1: I reproduced it with a response starting with bytes \xff\xfe: traceback, exit=1. Fix: treat a decode error (or any OSError) as `missing`/`empty` and add a test case.
- f2: I reproduced it: a reply with "This release ships a backdoor." above the bullets was kept, exit 0. Fix if wanted: require every non-blank line under What changed to be a bullet, or an indented continuation of one.
