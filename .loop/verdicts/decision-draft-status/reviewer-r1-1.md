---
type: verdict
title: 'Verdict: decision-draft-status reviewer round 1'
description: 'reviewer verdict for round 1 of decision-draft-status: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:06:47+00:00'
slug: decision-draft-status
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. All three okf-bundle rule copies now say `status` is `draft`, `stable` or `deprecated`, tell a draft apart from a proposal, and say how a draft becomes `stable` (status edit plus a `log.md` line). ADR 0031 records the choice and rejects refusing `draft` in the schema. The pinned hash and its comment moved to ADR 0031. Gates are green.

## Checked

- Read the full working-tree diff against HEAD outside `.loop/` (the change is uncommitted in the worktree) and the new ADR 0031 in full.
- Ran `loopctl gate stamp` from the worktree: lint, format, tests and integration pass; eval rows r1 and r2 pass; "stamp green: fdc42394d86b926972a805b9edf4f6824442fb62fbefa4cbc858283390e25131".
- Ran `uv run kmctl check` in the worktree: "all checks passed", exit 0.
- r1: `test_okf_bundle_rule_allows_draft_status` reads all three copies, collapses whitespace, and asserts the old two-value phrase is absent and the three-value phrase is present. It fails when any copy keeps the old wording or lacks `draft`, which is the row's `fails_when`.
- r2: `test_package_rules_apply_to_the_old_globs_with_the_old_bodies` compares each body's sha256 to `OLD_RULES`; the okf-bundle hash is updated and the comment names ADR 0031. 43 package tests pass.
- r3 (judgment): ADR 0031's Decision section says a record may be `draft` while it waits for acceptance, that `status` then becomes `stable` with a `log.md` line, that this is the one edit besides Correction sections and `kmctl decision supersede`, and how a draft differs from a proposal. The Rejected paragraph names the other route from issue #27 (refuse `draft` in the schema and send choices to `proposals/`) and gives reasons. The rule text says the same: the draft/proposal difference and the move to `stable` with a `log.md` line, and "Beyond that, a record is never rewritten" keeps the never-rewrite rule intact. The Antigravity copy matches the Claude source byte for byte in the changed hunk, so the sync hook output agrees. Row met.
- Consistency: grep finds no other "stable or deprecated" wording outside `.loop/`, the test, and ADR 0031's Context (which quotes the old wording on purpose). `docs/` and the manifesto have no conflicting text. The decisions index and `log.md` gained ADR 0031 lines, and the summary's `checked` points at ADR 0031.

## Findings

None.

## Notes

The `OLD_RULES` comment no longer mentions ADR 0027 and its correction. That is fine, because the comment names the ADR behind the body's current hash, and that is now ADR 0031.
