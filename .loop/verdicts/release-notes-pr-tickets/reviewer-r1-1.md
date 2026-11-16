---
type: verdict
title: 'Verdict: release-notes-pr-tickets reviewer round 1'
description: 'reviewer verdict for round 1 of release-notes-pr-tickets: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T07:00:09+00:00'
slug: release-notes-pr-tickets
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `_first_parent` now walks a non-release pull request merge's own first-parent line, excluding what main already had, and yields that line in place of the merge when it holds a ticket merge. Otherwise the merge stays one title bullet. The tests assert each row's fails_when, the gates pass, and drafting v0.13.0 and kmaudit-v0.1.0 from this repository lists the agent-audit tickets. Nothing blocks.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree myself. lint, format, tests, integration, eval-row r1 and eval-row r2 all pass, "stamp green: 2e9e84e55447f064218e9e649be370843ef517be8d5e1a7273ebe2ccc09fe1bf".
- Code read, scripts/release_notes.py. Release pull requests are kept out of expansion by `not _SKIP.match`. The pull request's walk excludes its first parent, so main commits that a sync on the branch brought in are not listed twice. Syncs on the branch are followed and then skipped in render as before. `_touched` diffs each ticket merge against its first parent on the integration branch, so the package filter sees only that ticket's paths. Order holds because the brought commits come newest first where the merge was, and render reverses the list. A pull request reached through a sync is expanded as well, because the sync's walk calls `_first_parent` again. A nested pull request that holds tickets expands the same way.
- r1: the three `pull_request_of_tickets` tests. They assert the title and `#53` are absent, each ticket appears exactly once and in merge order, the plain branch commit is under Other changes, the main commit synced into the branch appears once, and the `loop:` commit and the sync are absent. On the old code the title bullet would show, so the first test would fail.
- r2: `test_a_pull_request_without_tickets_keeps_its_title_bullet` asserts the title bullet stays and the commit is not under Other changes. The package-filter test asserts the kmctl-only ticket and the plain commit are left out of kmaudit's notes. The existing fixture's release pull request #2 still covers "release pull requests stay out". The whole file passes.
- Real data: from the worktree, `--package kmctl --ref v0.13.0 v0.13.0` gives 16 ticket bullets plus 4 plain agent-audit commits. `--package kmaudit --ref kmaudit-v0.1.0 kmaudit-v0.1.0` gives 12 tickets. `git log --first-parent ec504758^2 ^ec504758^1` holds 21 `Merge loop/` commits, which matches the "21 ticket merges" in the ADR correction.
- Consistency: the module docstring, the `_first_parent` docstring and ADR 0012's appended 2026-11-16 correction describe the new behaviour accurately. I found no other doc that still says each pull request is one bullet. The summary ack's `checked` block was rewritten by the tool.

## Findings

None.

## Notes

No test covers a pull request of tickets that reaches main through a sync merge, which is the usual way GitHub-merged pull requests arrive. The code handles it by recursion, and #53 sits directly on main's first-parent line, so I am not raising it as a finding.
