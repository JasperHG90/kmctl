---
type: verdict
title: 'Verdict: release-notes-hermes-reviewer-f2 reviewer round 1'
description: 'reviewer verdict for round 1 of release-notes-hermes-reviewer-f2: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:25:02+00:00'
slug: release-notes-hermes-reviewer-f2
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The stray-line check does what the plan asks. A non-blank line under What changed that is not a `- ` bullet, and is not indented after one, now sends the notes back to the draft with a warning naming stray-line. The draft's own lines, such as "None.", are exempt. The tests check the behaviour itself, and the gates are green. One wrapping nit in the ADR is left.

## Checked

- Ran `loopctl gate stamp` in the worktree myself: lint, format, tests, integration, eval-row r1 and eval-row r2 all pass; stamp green 81dab927a4613846f256fcf1417a0852c52934024770810eb4071c9184234b7a.
- Read the full diff (uncommitted in the worktree) and all of scripts/hermes_release_notes.py.
- r1: the three parametrized cases (intro, after-a-bullet, between-bullets) assert stdout is the draft byte for byte, that exactly one ::warning:: names "the stray-line check", and that --before is removed. Without `_stray`, the after-a-bullet and between-bullets lines are joined onto a bullet that has a reference, and the intro is skipped by `_bullets`, so all three would be kept. The tests would therefore fail on the old code.
- r2: the indented-continuation test asserts the wrapped rewrite comes out unchanged with no warning. The None test builds a draft whose What changed holds "None." (the shape scripts/release_notes.py:212 emits) and would fail without the `known` exemption. The 19 earlier tests still pass.
- Tried edge cases by hand with `check()`. An indented line before the first bullet is stray. An indented paragraph after a blank line under a bullet is kept: it is joined onto a bullet that carries a reference, which matches the plan's "indented under one". A tab-indented nested bullet is kept. A line with a reference that is not in the draft still hits ref-added first, so it falls back either way. A draft with no What changed gives `_stray` an empty section, so nothing crashes.
- The draft's non-bullet lines come only from scripts/release_notes.py ("None."), not from commit subjects, which always become `- ` bullets. So the exemption cannot be used to let a crafted line through.
- Consistency: the module docstring and ADR 0035 both describe the check correctly and say where it runs in the order. .okf/summary.md is only re-acked.

## Findings

- f1 (nit, non-blocking): the edited ADR 0035 bullet has one 104-character line ("under one, unless the draft has it too. Otherwise it prints the draft with a warning naming the failed") inside a paragraph wrapped near 72 columns. Rewrap the bullet. The meaning is fine.
