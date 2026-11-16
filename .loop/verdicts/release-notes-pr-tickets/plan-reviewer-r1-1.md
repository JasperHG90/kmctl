---
type: verdict
title: 'Verdict: release-notes-pr-tickets plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-notes-pr-tickets: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T06:45:08+00:00'
slug: release-notes-pr-tickets
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No risk found that could break the plan. The approach reuses the script's existing sync walk on the pull request's own first-parent line, and the real case (#53) has the shape the plan assumes. Problems, Goals and the single Outcome match the prose.

## Checked

- Read scripts/release_notes.py: `_first_parent` already follows a sync's second parent with the main side excluded, `_TICKET`, `_PULL` and `_SKIP` sort subjects, and the package filter diffs each commit against its first parent. So a ticket merge inside the pull request is filtered by its own diff, which is the behaviour the plan and r2 ask for.
- Ran `git log --first-parent ec504758^2 ^ec504758^1`: 815 commits, 21 `Merge loop/SLUG:` merges, one `Merge remote-tracking branch 'origin/main' into agent-audit` sync (1e11d268), five plain commits (`agent-audit: ...`, `audit: ...`, `prototypes: ...`) and three `operator: manual commits`. The rest are `loop:` commits. The sync's second parent is reachable from ec504758^1, so excluding main's side (as the plan says, "commits it brought in that main did not have") keeps main's own commits out. `_SKIP` already drops the loop, sync and placeholder commits.
- Drafted v0.13.0 today with `--ref v0.13.0`: one bullet, "kmctl and kmaudit as two workspace packages... (#53)", confirming P1.
- #53 sits directly on main's first-parent line between v0.12.2 (#52) and the v0.13.0 release PR (#54), so the previous-tag exclusion plus ec504758^1 bounds the walk correctly. kmaudit-v0.1.0 has no previous tag, so only ec504758^1 bounds it.
- Downstream: scripts/hermes_release_notes.py checks that the rewrite keeps the draft's set of `(`slug`)`/`(#N)` refs. Ticket bullets carry slug refs, so more bullets do not break that check. release-tag.yml's late-commit check walks main's first-parent line on its own and is not changed by this plan.
- Facts: one problem (one cause), one goal, one behaviour outcome that ships alone, needs none, touches cover the script (its docstring included), its tests and ADR 0012, matching the prose.

## Findings

None.

## Notes

These are build-time details, not plan risks. Choosing between "one bullet per ticket" and "keep the title bullet" means scanning the pull request's line before emitting, while `_first_parent` yields the merge before what it brought in. The expansion should also apply when the pull request is reached through a sync, since GitHub-merged pull requests usually arrive that way. A `Merge pull request` inside the integration branch's line is not covered by the plan; #53 has none.
