---
type: verdict
title: 'Verdict: kmaudit-skills-mcp plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmaudit-skills-mcp: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:48:02+00:00'
slug: kmaudit-skills-mcp
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved. Putting the agents in a Claude-only sub-package works: APM 0.33.0 narrows each package's deploy targets to the ones its own apm.yml declares. One small touches gap is left: the overview, the manifesto and two ADRs' sources describe the agents as they are today. Fixing it means revising the plan, not rethinking it.

## Checked

- How APM limits a sub-package to its targets. In apm-cli 0.33.0 (the version conftest's apm_install pins), `install/services.py::integrate_package_primitives` calls `install/target_filter.py::resolve_effective_package_targets`. That function intersects three sets: the project's active targets, the consumer entry's subset and the package's declared `targets`. A package with `targets: [claude]` gets no OpenCode or Antigravity deploy, agents included. kmctl's `apm/claude` (`kmctl-claude`, `targets: [claude]`) and `apm/antigravity` already depend on this for rules and hooks, and the apm-per-package evidence lock shows nested `./claude` sub-packages installing from a path inside the repo (`packages/kmctl/apm/claude`, 4 files deployed). So `packages/kmaudit/apm/claude` with the two agents reaches `.claude/agents/` only. The plan's integration check (agents in .claude/agents/, none in .opencode/agents/) tests exactly this.
- kmctl's translation: `opencode.agent_paths/agent_files` and `antigravity` plugin building read only `agents_dir()` (kmctl's own `.apm/agents` or wheel `_agents`) plus okf's apm_modules folder. Once the files are gone from kmctl's package, the translation skips them, and only the tests' hard-coded lists need changing. All of those files are in touches now. The Antigravity plugin folder is deleted and rebuilt with `rmtree` (antigravity.py:328), so a project that upgrades loses the stale translated copies.
- No other place names the agents outside the touched files except the .okf pages in p3, kmaudit's briefing (it names only the skill names, which stay) and test_audit_guard.py (it tests the guard, which stays).
- The dependencies (apm-per-package, kmaudit-mcp) have not landed on this branch yet. `apm/` is still at the root. The plan's paths assume they have landed, which matches its depends_on.

## Findings

- p1: resolved. The Claude-only sub-package plus the skill's own batch fallback gives OpenCode and Antigravity a clear path, and kmctl no longer has to translate kmaudit's agents.
- p2: resolved. The kmctl modules and tests and kmaudit's cli.py are now in touches.
- p3: open. overview.md and manifesto.md describe the agents as shell agents in kmctl's package, and ADR 0037 and 0040 cite the old agent files as sources. None of these are in touches.

## Notes

The facts (one behaviour outcome, P1, G1) match the prose. Nothing here calls for a split.
