---
type: verdict
title: 'Verdict: upgrade-from-v0-12-docs reviewer round 2'
description: 'reviewer verdict for round 2 of upgrade-from-v0-12-docs: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T20:19:18+00:00'
slug: upgrade-from-v0-12-docs
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed. The Upgrade section now says kmctl's own audit is unchanged and
that kmaudit is a new, separate package you install apart. That agrees with
the README's intro, its `/audit` entry and the shipped code. The gates are
green and nothing else changed.

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests, integration and eval-row r1 all pass; stamp green c5667b7b6b06b5afa2b78a4e45863eb708296196c5eb37852c0b98c8a69046e5.
- The new sentence at packages/kmctl/README.md:222-226 against the code: `action.yml` still has `mode: audit` and the `audit:` input (docs-vs-code), and `packages/kmctl/apm/.apm/skills/audit` and `agents/kmctl-auditor.md` still exist, so "unchanged" is true. The description of kmaudit matches the first lines of packages/kmaudit/README.md.
- Against the rest of the README: the intro (lines 12-18) calls the audit agent opt-in and says kmctl and kmaudit "install apart"; the `/audit` entry (line 314) still describes kmctl's own audit. No contradiction.
- The staged diff: the only change since round 1 is that README paragraph. The steps, the how-to and the tests are as they were in round 1.

## Findings

- f1: resolved at packages/kmctl/README.md:222-226, which now says kmctl's own audit is unchanged and kmaudit is a new, separate package.

## Notes

The docstring of `test_upgrade_docs_send_auditing_to_kmaudit` (packages/kmctl/tests/test_docs.py) still calls kmaudit "the new home of auditing", which repeats the overstatement f1 fixed in the README. The round 2 fix did not touch it, so it falls outside this narrow round. It is worth rewording in a later pass, to something like "kmctl's README links kmaudit's README".
