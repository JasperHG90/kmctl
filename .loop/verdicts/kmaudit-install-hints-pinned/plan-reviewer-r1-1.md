---
type: verdict
title: 'Verdict: kmaudit-install-hints-pinned plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-install-hints-pinned: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:44:18+00:00'
slug: kmaudit-install-hints-pinned
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. The plan lists no risks, and I found none that would make the approach fail.

## Checked

- `INSTALL` is a module constant in `packages/kmaudit/src/kmaudit/steps.py:37` and `judge.py:96`. Its only users are `check_verbs.py:54/547` (imported from steps), `ui.py:603/621` (imported from judge) and `judge.py:544/548`. No test imports `INSTALL`. All four files are in `touches`.
- The tracing bug is real. `judge.py:548` tells the user to install the `kmaudit[tracing]` extra, then prints `INSTALL`, which has no extra.
- kmaudit already reads its own version with `importlib.metadata.version("kmaudit")` (`cli.py`, `mcp_server.py`), and hatch builds that version from the version file. A wheel built from tag `kmaudit-vX.Y.Z` therefore reports X.Y.Z, and the hint names a tag that exists. apm-per-package keeps the same `[tool.hatch.version]` mechanism and only points it at `packages/kmaudit/apm/apm.yml`, so the runtime version survives the move.
- `_KMAUDIT_INSTALL` in `scripts/release.py` already matches the docs' `kmaudit[tracing] @ git+...#subdirectory=packages/kmaudit` line (`docs/commands.md:438`). The release workflow's kmaudit `git add` (`release.yml:326`) is the one place to stage it.
- Repo-wide, the only other kmaudit install line is `.github/release-notes-kmaudit.md`, which uses `$tag` and is filled in per release. So the plan's list of hints is complete.
- The facts (P1, G1, O1) match the prose, and the touches cover what the prose changes.

## Findings

None.

## Notes

- kmaudit-skills-mcp (no ordering between the two tickets) also changes `set_kmaudit_version`, the kmaudit staging in `release.yml` and `docs/commands.md`. It adds an `@kmaudit-vX.Y.Z#subdirectory=packages/kmaudit` ref in kmaudit's apm.yml. Whichever lands second merges the refusal and staging logic. Make the "refuses when missing" check require at least the tracing line rather than an exact count of regex hits in commands.md, so a line the other ticket adds does not trip it.
- The intent says the function works "the way kmctl's hook hint does". kmctl's hook hints in `hooks.json` are pinned by `release.py`. The version-derived ref the plan means is `kmctl.plugin.package_ref()` / `cli_version()`. The approach is sound either way.
- Decide how a pre-release such as `0.2.0rc1` is handled. It has a `kmaudit-v0.2.0rc1` tag, so it should name its ref like a final release.
- The one `behaviour` outcome covers both the runtime hint and the release-time docs pin. The ticket is small enough that keeping them together is fine.
