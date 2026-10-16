---
type: verdict
title: 'Verdict: apm-only-install plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of apm-only-install: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T20:22:28+00:00'
slug: apm-only-install
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds. Each of the four listed risks is settled by a spike whose evidence answers it: layout and rule scoping (apm-only-install/1, repo-uses-apm/3), user scope (apm-only-install/2), and skip-over-hand-made-skills (apm-only-install/3 to 5). The code the plan names exists and behaves as the plan says. Two gaps in migration remain. Both concern repositories that already use kmctl through a route this ticket removes, and either can leave old content loading next to the new install. Both are revisions, not a rethink, and each can be settled with a spike.

## Checked

- Read the plan, the empty eval (no rows yet), spikes apm-only-install/1 to 5, repo-uses-apm/3 and kmctl-doctor/1 (READMEs, and spike 1's script for the apm.yml entry form).
- Spike 1's consumer entry had no `ref:`. The cached apm-cli 0.33.0 source (`apm_cli/deps/apm_resolver.py` near line 57) reads `ref` from a git object entry, so the planned `{git, path: apm, ref: v<version>}` form is accepted.
- APM's hook merge (`apm_cli/integration/hook_integrator.py`) removes only entries it tagged with `_apm_source` and keeps user entries. So a SessionStart entry that kmctl writes survives later `apm install` runs, including the run that deploys okf's Stop hook. The design holds, provided kmctl's entry carries no `_apm_source` (see p1).
- `src/kmctl/plugin.py` has `skills_dir`, `_cause`, `PluginError`, the staging, the `okf_source` and `extraKnownMarketplaces` code and the `claude plugin` calls the plan removes. The test files, `action.yml`, `.github/workflows/knowledge-audit.yml`, both release workflows and `pyproject.toml` (force-include, hatch version path, and `cache-keys`, which also names plugin.json) reference what the plan says. `kmctl new decision` and `kmctl decision supersede` exist.

## Findings

- p1: ADR 0013-route consumers are not migrated. Proposed spike: in a consumer that installed v0.3.0 through the string entry, replace the entry with `{git, path: apm, ref}` for the new layout and run `apm install`, then write a plain kmctl SessionStart entry. Check three things. (a) Does APM treat the two entry forms as the same package, and what happens if both are present? (b) Does APM remove the old package's hook entry and its stale files? (c) Does kmctl's entry survive a second `apm install`? The plan should then say that install replaces any existing kmctl entry, whatever its form, and how the writer treats an APM-owned briefing entry.
- p2: The okf plugin and the marketplaces left over from old installs. Proposed spike: with claude, install kmctl@kmctl the old way, then run `claude plugin uninstall kmctl@kmctl --scope project`. Check whether okf@scaccogatto stays installed and enabled, and what stays in `.claude/settings.json` (`enabledPlugins`, `extraKnownMarketplaces` for kmctl and scaccogatto). The plan should then name what install also removes, or what it reports.

## Notes

The ticket is large (37 files plus a CLI rewrite), but it is one move with one contract, and only two real risks remain, so I do not recommend a split.
