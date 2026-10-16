---
type: verdict
title: 'Verdict: apm-distribution plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of apm-distribution: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T10:18:30+00:00'
slug: apm-distribution
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. Each of the three listed risks is settled by a spike that answers it. The gap you asked about, local git server versus GitHub, does not change the route: in APM 0.33.0, `{git: parent, path: plugin}` takes its host, repo and ref from the package that declares it, and subfolder packages are fetched over git on both hosts.

## Checked

- Spikes 1 to 5: README outcomes, the stdout from spike 5, and the scripts. Spike 1 failed on transport and spike 2 replaces it. Spike 2 shows `plugin/` installs as a subfolder package with no apm.yml: 7 skills, the agent and the hook. Spike 3 shows a subfolder consumer gets none of the root dependencies, and that `version` is required. Spike 4 shows why `plugin/` must not get an apm.yml: the agent is dropped. Spike 5 shows the meta package (M) gets everything, with the lock listing only o/m/apm, o/m/plugin and okf-skills, and the hook's `kmctl briefing` exits 0.
- GitHub versus local server, checked in the APM 0.33.0 source (`deps/apm_resolver.py` `expand_parent_repo_decl`, `_inherit_remote_parent_fields`) and by parsing offline with the spike venv's APM. `JasperHG90/Knowledge-management/apm#v0.2.0` parses to host github.com, repo `JasperHG90/Knowledge-management`, subfolder `apm`, ref v0.2.0. Expanding `{git: parent, path: plugin}` against it gives github.com, the same repo, subfolder `plugin`, and ref v0.2.0, so the plugin is fetched at the same tag. The only fields that change between hosts are host, port and scheme, which come from the parent. Spike 5's run used the same code path.
- The plan depends on two other tickets. release-flow's `scripts/release.py` has `current` and `set_version`, and reads `plugin/.claude-plugin/plugin.json` as the one version source, so adding the apm.yml files fits it. repo-uses-apm's root apm.yml has `version: 0.1.0` and its jasperhg90/skills entries under plain `dependencies.apm`, as the plan assumes. ADR 0012 is the last number in release-flow, so 0013 is free.

## Findings

None.

## Notes

These are not blocking. They are for the builder and the docs:
- The repo is private. A consumer, and the Done-when check after the release, needs GitHub auth for APM (a token or gh login) to clone it. This applies to any git route, so the plan holds. The how-to page should say so while the repo stays private.
- APM refuses `git: parent` at user scope ("not supported at user scope", `install/package_resolution.py`). `apm install -g` will not work for the meta package. The docs should show only the project-scope install.
- Spike 5 never ran the GitHub install against a real tag. The Done-when step after the release is the first real test of it. From the code reading above, I expect it to pass.
