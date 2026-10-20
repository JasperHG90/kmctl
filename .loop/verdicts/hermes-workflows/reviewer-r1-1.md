---
type: verdict
title: 'Verdict: hermes-workflows reviewer round 1'
description: 'reviewer verdict for round 1 of hermes-workflows: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-20T08:55:17+00:00'
slug: hermes-workflows
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The workflows, prompts and okf skill match their workspace sources except for the intended edits (kmctl's areas, `apm.yml` for `aim.toml`, the short triage format, and the inline Python moved to `scripts/hermes_triage.py`). The script is a faithful port plus the cut, and every gate and eval row is green. One claim in ADR 0035 is false on a security point: a member's `/hermes` on a fork's pull request does run with the key against the fork's code. That needs correcting before commit, and I want to see the fix because it touches the security story.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and rows r1 to r6 all pass, stamp green 2a50e69f179ea4617a4fb0cefff91479d773d3580ca283698b20ae1b35593b5f.
- `prek run --all-files`: every hook passes, including kmctl check --fix, okf validate --strict and ruff. The tree was unchanged afterwards.
- Diffed each copied file against /home/vscode/workspace/.github. The okf skill is byte-identical. hermes-interactive.yaml is identical. The prompt and triage workflow diffs are only the intended edits.
- r1: the tests assert `trigger_phrase == '/hermes'`, the `/hermes` contains-check, the member/owner/collaborator gate in both job conditions, and no `@hermes` in either workflow or prompt. These fail when the row's `fails_when` holds.
- r2: the test asserts the `.hermes-trusted` checkout uses the default branch and that `system_prompt_file` and `skills_dir` both sit under it.
- r3: the existing SHA-pin test is parametrized over both new workflows and selected by `-k`.
- r4: a 40-line, more-than-2000-character input; the test asserts the result is at most 800 characters and that every kept line is a whole original line, so a mid-line cut fails it.
- r5: the tests assert the trailer is gone, `made-up` is dropped, priority comes first, and no trailer means no labels.
- r6: the tests assert "200 tokens" is in the prompt and that each area maps to a real top-level folder. action, apm, starter, src, tests, scripts and docs exist, okf maps to .okf and ci to .github.
- r7 (judgment): ADR 0035 is Accepted and is in the index. It cites ADR 0017 and keeps 0017's audit decision ("ADR 0017's reasons against Hermes still apply to the audit"), so it does not contradict it. The row holds, apart from the false consequence in f1.
- Read `scripts/hermes_triage.py` in full. It cuts after stripping the trailer, keeps labels in order without duplicates, and returns exit 1 when the response file is missing. The workflow supplies ISSUE_NUM (step env) and TRIAGE_AREAS (job env), and the triage checkout is the default branch, so the script that runs is the trusted one.

## Findings

- f1 (blocking): Under Consequences, ADR 0035 says "Neither job runs on a fork's pull request with the key". hermes-interactive.yaml only skips `pull_request_review_comment` from forks. An `issue_comment` on a fork PR from a member still runs in the base repository's context with secrets and checks out `refs/pull/N/head`. The prompt and skills are trusted, but the code Hermes reads is not. Correct the ADR to say what really happens: a member's `/hermes` on a fork PR runs with the key against the fork's code, and only the member gate stands between it and prompt injection. Do not add a fork guard to the workflow; the operator chose to keep it as it runs in the workspace repository.
- f2 (non-blocking): this is a hardening change to the triage workflow. The value is a path the action sets, so the risk is low, but passing it through env costs nothing and matches the source.

## Notes

- `cut()` falls back to a mid-line cut when an over-long comment has no line break in its first 800 characters. That is a reasonable fallback, and the prompt asks for separate lines, so it is not a finding.
- `main()` (the `gh` calls) has no test. The rows do not ask for one, and it matches the source's logic.
