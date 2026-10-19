---
type: verdict
title: 'Verdict: release-cache-off plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-cache-off: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T01:07:02+00:00'
slug: release-cache-off
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan holds. Five setup-uv steps still set `enable-cache: true` (release.yml lines 55, 114, 130, 174; release-tag.yml line 35), and nothing in either workflow depends on the cache, so turning it off costs only download time. The security premise is sound, and the eval rows match the intent.

## Checked

- The premise: knowledge-audit.yml runs on `workflow_dispatch` and `schedule`, so on `main`. Its agent job already has `enable-cache: false` and `persist-credentials: false`, but the agent runs shell commands as the runner user with passwordless sudo. It could therefore get the runner's cache token and save any key in `main`'s cache scope. The release jobs run on `main` (release.yml by dispatch, release-tag.yml on push to `main`), and they would restore entries from that scope under setup-uv's key. ADR 0017's 2026-10-17 Correction already says the cache is off in both audit jobs; the release side is the gap.
- Nothing relies on the cache: no `--offline`, no `UV_CACHE_DIR`, no `actions/cache` and no other cache input in either release workflow. `uv tool install rust-just` and `uv run` work from a cold cache. ci.yml has run with the cache off since `test_ci_actions_pinned_and_uv_cache_off`.
- The tests: tests/scripts/test_workflows.py already loads RELEASE and RELEASE_TAG, with `_load`/`_steps` helpers and `[RELEASE, RELEASE_TAG]` parametrisation, so r1 fits there. Today `-k cache` selects nothing in that file, so r1 fails until the test exists, which is correct. r2's `-k cache_record` needs a test with that name; the plan's builder writes it. r3 is the full suite.
- ADRs 0012 and 0017 both exist and already carry dated Corrections, so another Correction follows the pattern in .claude/rules/okf-bundle.md.

## Findings

None.

## Notes

- audit-drift-followup also adds a Correction to ADR 0012 and touches `.okf/log.md` and the summary. Whichever ticket lands second will need a small rebase. That is not a risk to this plan.
- The Correction also needs a `.okf/log.md` line and a summary update or `kmctl summary ack`. r3's `tests/test_summary.py` this-repo tests and the pre-commit gates catch a miss.
