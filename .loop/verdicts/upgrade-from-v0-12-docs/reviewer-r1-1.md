---
type: verdict
title: 'Verdict: upgrade-from-v0-12-docs reviewer round 1'
description: 'reviewer verdict for round 1 of upgrade-from-v0-12-docs: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T20:09:43+00:00'
slug: upgrade-from-v0-12-docs
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The upgrade steps are right and in the right order on both pages, and they
match the code and v0.12.2's behaviour. The gates are green. One sentence
says something false: it tells users that auditing moved to kmaudit, but
kmctl's audit features from v0.12 still ship unchanged. I marked it blocking
because the new wording has to say exactly what kmaudit is next to what
kmctl still does, and a second wrong claim would go straight to users.

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests, integration and eval-row r1 all pass; stamp green e67f2f25...
- Step order against the code. v0.12.2's `pin.py` hands off with `uvx --from git+...@COMMIT` and no subdirectory, and its `kmctl_package` matches only `virtual_path == "apm"`, so an old CLI cannot run a later pin. That makes "install the CLI first" true. The new `pin.uvx_source` adds `#subdirectory=packages/kmctl` only after `LAST_ROOT_RELEASE = v0.12.2`, and `PACKAGE_PATHS` matches both folders, so the new CLI still hands `plugin patch` and `doctor` to v0.12.2 until `apm install` moves the lock. That makes "doctor last" true.
- Starter: `upgrade ref` runs `copier update --data kmctl_ref=...` and then `just kmctl install`. The rewritten `kmctl` recipe installs `kmctl_src` with the subdirectory fragment when the CLI on PATH is older, and `apm.yml.jinja` writes `path: packages/kmctl/apm` for refs after v0.12.2. The v0.12.2 starter has the same recipe, so `just upgrade vX.Y.Z` works from a v0.12 project.
- Action and hook: the `action.yml` inputs and the `.pre-commit-hooks.yaml` hook id are unchanged since v0.12.2. Only the internal install path and `additional_dependencies` changed, so "change only their tag" holds.
- Row r1: `test_upgrade_from_v0_12_gives_the_steps_in_order` cuts out each page's section and finds the CLI install (`#subdirectory=packages/kmctl`), then `path: packages/kmctl/apm`, `apm install` and `kmctl doctor`, each after the one before. It fails if doctor comes only before apm install or if a step is missing. It also asserts `path: apm`, `ref: v` and `just upgrade`. `test_upgrade_docs_send_auditing_to_kmaudit` asserts the link. The link was already in the README intro (line 16), so this test passes even without the change, but it still checks what the row asks for. Three tests pass.
- Prose: plain and short. The how-to shows the new entry inline instead of as a block, but the git URL does not change, so path plus ref is the full change.

## Findings

- f1 (docs, blocking): the "moved to its own package" sentence at packages/kmctl/README.md:222 is false. v0.12.2's action audit mode, `/audit` skill and auditor agent all still exist; see `action.yml` `audit:` input (docs-vs-code is still listed), `packages/kmctl/apm/.apm/skills/audit`, `packages/kmctl/apm/.apm/agents/kmctl-auditor.md`. Suggested fix: say kmaudit is a new, separate package that checks the claims a folder of docs makes against the code, that you install it apart if you want it, and that kmctl's own audit (the action's audit mode and `/audit`) is unchanged. The plan's line "Auditing a folder of docs is now kmaudit's" overstates this too, but the plan's goal (a v0.12 user can upgrade from the docs) survives a correct sentence, so this does not invalidate the plan.

## Notes

The how-to has no kmaudit line, which matches the plan's scope.
