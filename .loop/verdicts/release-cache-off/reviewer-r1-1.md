---
type: verdict
title: 'Verdict: release-cache-off reviewer round 1'
description: 'reviewer verdict for round 1 of release-cache-off: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T01:18:38+00:00'
slug: release-cache-off
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. All five setup-uv steps (four in release.yml, one in release-tag.yml) now set `enable-cache: false`. The new tests fail when any one of them reverts. ADR 0017 has an accurate dated Correction. Nothing blocks.

## Checked

- Ran `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2 and r3 all pass, "stamp green: 51fd73844f6df2b600b6cb5b1b808cff6011d1feb4d2c4271c93dad97c496adf".
- Workflows: grepped both release workflows for `uses:` and `cache`. The only cache source is setup-uv, and all five steps are off. No step uses actions/cache, a setup-* cache or `cache-dependency-glob`, so nothing else relied on the cache. Turning it off only costs download time (`uv tool install rust-just`, `uv run`).
- r1: mutation-tested on a copy of the worktree outside it. Setting the release-tag step to `true` fails `[release-tag]`. Dropping the `with:` block from the last release.yml step (key missing) fails `[release]`. The test compares with `is False`, so a missing key or a string value also fails.
- r2: cutting the 2026-10-19 Correction from the copy fails `test_release_workflows_cache_record_names_the_reason`. The 2026-10-17 Correction does not satisfy it on its own, because it names knowledge-audit.yml, not release.yml.
- r3: the full suite passes in the stamp.
- Consistency: the Correction matches the plan's intent: the shell runs as the runner's user with passwordless sudo, so it can reach the runtime token, and the scheduled or dispatched audit runs on main, so its cache entries land in main's scope where release jobs could restore them. "As CI's already did" holds: ci.yml and knowledge-audit.yml already set `enable-cache: false`. The log line is dated and correct. The summary's ADR 0017 claim ("takes any provider and never runs beside a GitHub token") still holds, so the ack is fair.

## Findings

None.

## Notes

The `.loop/` entries in `git diff main` come from main's loop state moving ahead of the worktree. They are not part of this change.
