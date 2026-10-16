---
type: verdict
title: 'Verdict: release-flow plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-flow: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T06:00:16+00:00'
slug: release-flow
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. Both listed risks are settled by evidence that answers them. I found no unlisted risk that would force a rethink; what is left are build details.

## Checked

- Risk 1 (one version source): spike:release-flow/1 exited 0 with fail=0. `uv build` gave a 0.2.0 wheel and sdist, the sdist holds `plugin/.claude-plugin/plugin.json`, a wheel built from the sdist is 0.2.0, and `uv tool install` both from a git tag and from a `git archive` folder printed `kmctl 0.2.0`. That covers every install path the plan names, including the `action.yml` path (`uv tool install "${{ github.action_path }}"`, action.yml). The `"version"` regex matches exactly one key in `plugin/.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json` has no version, so there is no second source.
- Risk 2 (GITHUB_TOKEN can open PRs): spike:release-flow/3 reads `can_approve_pull_request_reviews: true`. I re-read it today with the same result. spike:release-flow/2 is a void run, as the plan says.
- Unlisted risks I checked: `main` has no branch protection and no rulesets, so a version PR with no checks can still merge, and a person merging it starts release-tag.yml. `src/kmctl/__init__.py` and `src/kmctl/plugin.py` read the version through `importlib.metadata`, and nothing reads `[project] version` from `pyproject.toml` (the only read of pyproject in tests is the pytest config, in test_network_retry.py). Tests that need the claude CLI skip without it, and tests that commit to git set their own author and committer, so `just test` should run on a bare runner. I also compared the plan with loop-harness's `release.yml` and `release-tag.yml`: the hatch-vcs and floor/ST-11 parts it drops are the ones kmctl has no use for.

## Findings

None.

## Notes

Build details, not plan risks:
- ubuntu-latest may not ship `just`. Install it, or have release.yml run the uv commands the recipes run.
- loop-harness's bump step runs `git add plugin/.claude-plugin/plugin.json` only. kmctl's `release.py set` also rewrites doc lines, so the commit must add those too.
- Doc pins: `set` rewrites an `@vX.Y.Z` pin, but README.md:18 and docs/tutorials/get-started-with-kmctl.md:19 have no ref today, and the Knowledge bullet pins only the how-to. Decide whether this ticket pins all 5 lines and whether `set` fails when it finds fewer. Pinning `@v0.2.0` before that tag exists leaves the docs on main pointing at a missing tag until the first release runs.
- uv's default cache keys do not include `plugin.json`, so a local `uv run kmctl --version` may keep reporting the old version after a bump until the package is reinstalled. Adding `[tool.uv] cache-keys` with the manifest fixes that. It does not affect CI, which installs fresh.
