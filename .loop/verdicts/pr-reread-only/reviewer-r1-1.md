---
type: verdict
title: 'Verdict: pr-reread-only reviewer round 1'
description: 'reviewer verdict for round 1 of pr-reread-only: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-27T11:05:42+00:00'
slug: pr-reread-only
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks: one task, one shipped prompt, read-only tools, audit mode only on a same-repository pull_request, and this repository's workflow runs the reread on its pull requests with the token only in the publish job. One correctness gap blocks. A pull request that renames or moves a source file leaves every page naming the old path out of scope, and that is exactly the page most likely to be outdated now. The agent's one job is to catch this case. The fix is small: pass `--no-renames` to the diff, plus a test.

## Checked

- Read the diff `main...HEAD` and, in full, action/agent.py, action.yml, .github/workflows/knowledge-audit.yml and action/prompt.md.
- Reproduced f1 on a scratch git repository: docs/p.md has the source src/a.py, the branch runs `git mv src/a.py src/b.py`, `git diff --name-only --relative main...HEAD` prints only `src/b.py`, and `agent.py run --model test --base main` writes "No page ... names a file this change touched".
- Security of the PR path: in consumer repos the agent and prompt come from `github.action_path` (the pinned action), and `uv run --no-config` ignores the checkout's uv config. The agent job has no token: persist-credentials is false and refuse_tokens checks the environment and the extraheader. Publish runs on a fresh runner with only the artifact. In this repo, publish runs the PR's own action/agent.py with pull-requests: write. A same-repo author can already push workflow changes that get the same token, so this gives them nothing new, which is ADR 0057's reasoning. Fork and Dependabot PRs are skipped by the job conditions. No escalation found.
- changed_pages: `--relative` with a subfolder `path` gives paths relative to that folder, matching pages' sources. Paths outside the folder drop out, which is correct. A folder source matches as a prefix. Deleted files are listed, so their pages stay in scope. Renames are not handled (f1). The index.md exclusion also drops a docs page named index.md. This repo's docs folders use README.md, so that is a note, not a finding.
- Plan-review round-2 fix: in the plan, O3 is `kind: support`, O5 has `needs: O3, O4`, and tests/test_audit.py is listed under O3's touches. The fix holds.
- Gates: the coordinator asked me to skip long-running work because the stamp at 324e9a33 already ran the gates green, so I did not rerun `loopctl gate stamp` myself. I did not open every eval row's test, so the rows are not judged in this round.

## Findings

- f1 (bug, blocking): by default, `git diff` detects renames, and `--name-only` then prints only the destination path. source_matches never sees the old path, so a page naming it silently drops out of scope, and the run may call no model at all. Use `--no-renames` so both the old and the new path are listed, and add a test with a renamed source on a real git repository. The bug predates this change (changed_decisions had it too), but this change makes changed_pages the action's only job.
- f2 (nit): delete the second `_number` at action/agent.py:209-215.

## Notes

The action and workflow look consistent with each other and with the plan. I did not finish the docs-accuracy pass over the tutorial and how-to before the coordinator asked me to wrap up, so round 2 should look at those.
