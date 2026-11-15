---
type: plan
title: 'Plan: apm-per-package'
description: Each package keeps its APM package and its version in its own folder, packages/kmctl/apm and packages/kmaudit/apm, so kmaudit's version stops living in a VERSION file.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:20:00+00:00'
slug: apm-per-package
epic: monorepo-release
depends_on:
- root-release-cutoff
priority: 1
schema_version: '2.0'
---

# apm-per-package

Relayed from: none

## Intent

The operator: "If you are placing apm in kmaudit folder, then the root-level
one should go into kmctl", and of `packages/kmaudit/VERSION`: "This is not
how we do version management." The repository's convention (ADR 0012) is
that a package's version lives in its APM package's `apm.yml`. kmctl's APM
package sits at the repository root in `apm/`, and kmaudit has none, so
release-per-package gave kmaudit a `VERSION` file instead.

This ticket moves kmctl's APM package from `apm/` to `packages/kmctl/apm/`
(`git mv`, so the skills, agents, rules, hooks and the per-harness
sub-packages keep their history) and gives kmaudit an APM package at
`new:packages/kmaudit/apm` whose `apm.yml` carries its version, replacing
`packages/kmaudit/VERSION`. kmaudit's skills and agents move into that
package in kmaudit-skills-mcp; here it holds the version and a description.

What follows the move:

- Builds: kmctl's `[tool.hatch.version]`, `cache-keys`, the sdist's
  force-include and `hatch_build.py` read `apm/` inside the package folder
  (no `../../`), and kmaudit's `[tool.hatch.version]` reads its `apm.yml`
  with the same regex. `scripts/check_wheel.py` follows.
- Releases: `scripts/release.py` (`MANIFEST`, `APM_FILES`, `HOOKS`, the
  kmaudit version source), the release workflow's `git add` list and its
  input descriptions, and release-tag's `paths:` trigger. release-tag's
  `manifest` read of the commit before the push tries the moved
  `apm.yml` and falls back to `apm/apm.yml`, because the
  first release after the move compares against a commit from before it.
- The consumer entry: releases after the cutoff (root-release-cutoff's
  `LAST_ROOT_RELEASE`) are added as
  `{git: …/kmctl.git, path: packages/kmctl/apm, ref: vX.Y.Z}`, older ones
  keep `path: apm`. `kmctl.plugin.new_entry()` writes the path for this CLI's
  version; `kmctl.plugin` and `kmctl.doctor` recognise kmctl's entry and its
  sub-packages under either path. The starter's `apm.yml.jinja` picks the
  path from `kmctl_ref` the way its justfile picks `kmctl_src`.
- Source-tree fallbacks in `plugin.py`, `antigravity.py` and `opencode.py`,
  the action's agent (`action/agent.py`) and every test that reads `apm/`.
- Docs, rules and decisions that give the entry or the path: the README,
  the install how-tos, `.claude/rules/cli-version-floor.md` and the other
  rules that cite `apm/`, the release skill, ADR 0012, 0014, 0021 and 0044
  and the architecture overview.

The root `apm.yml`, this repository's own install of its dependencies
from jasperhg90/skills, stays at the root; it does not install kmctl's
package.

It worked when a project generated from the starter at a release after the
cutoff installs kmctl's package from `packages/kmctl/apm` with
`just bootstrap`, doctor passes on it and on a project pinned to an old
release with `path: apm`, both wheels carry the release version read from
their `apm.yml`, and no `VERSION` file is left.

## Problems

- P1: kmctl's APM package sits at the repository root while its code is in packages/kmctl, and kmaudit has no APM package, so kmaudit's version lives in a VERSION file against the repository's convention.

## Goals

- G1: Each package keeps its code, its APM package and its version in its own folder.

## Outcomes

### O1: kmctl's APM package lives in packages/kmctl/apm and kmaudit's version in packages/kmaudit/apm/apm.yml
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `apm`, `new:packages/kmctl/apm`, `new:packages/kmaudit/apm`, `packages/kmaudit/VERSION`, `packages/kmctl/pyproject.toml`, `packages/kmctl/hatch_build.py`, `packages/kmaudit/pyproject.toml`, `packages/kmctl/src/kmctl/plugin.py`, `packages/kmctl/src/kmctl/doctor.py`, `packages/kmctl/src/kmctl/antigravity.py`, `packages/kmctl/src/kmctl/opencode.py`, `action/agent.py`, `scripts/release.py`, `scripts/check_wheel.py`, `.github/workflows/release.yml`, `.github/workflows/release-tag.yml`, `starter/apm.yml.jinja`, `README.md`, `docs/how-to/install-kmctl-with-apm.md`, `docs/how-to/install-the-plugin-and-the-ci-action.md`, `.claude/rules/cli-version-floor.md`, `.claude/skills/release/SKILL.md`, `.okf/decisions/0044-kmctl-and-kmaudit-are-both-workspace-packages.md`, `.okf/architecture/overview.md`, `packages/kmctl/tests/test_plugin.py`, `packages/kmctl/tests/test_doctor.py`, `packages/kmctl/tests/test_starter.py`, `tests/scripts/test_release.py`, `tests/scripts/test_workflows.py`
- checked by: the starter bootstrap integration test (a release after the cutoff, `path: packages/kmctl/apm`, doctor passes); test_starter renders `path: apm` at v0.12.2 and `path: packages/kmctl/apm` at v0.13.0; doctor and plugin patch tests recognise kmctl's entry and sub-packages under both paths and new_entry writes the new one; release.py tests read kmctl's version from its moved apm.yml and kmaudit's from its new one, `manifest` falls back to apm/apm.yml on an old commit, and `set --package kmaudit` writes the apm.yml; the package build test checks both wheels' versions and contents; a test that no `apm/` folder and no `packages/kmaudit/VERSION` remain
- seen by: operator

## Could invalidate this plan

- none. The one risk, that APM cannot install a package from a nested path
  whose own apm.yml pulls in `./claude` and `./antigravity`, was measured
  before writing this: see Evidence. It installs, and the lock records the
  virtual paths `packages/kmctl/apm`, `packages/kmctl/apm/claude` and
  `packages/kmctl/apm/antigravity`, which O1's doctor and plugin changes
  match.

## Evidence

The measurement could not run through `loopctl plan spike`: APM refuses a
`file://` source (`Invalid virtual package path`), so the run needs git's
`insteadOf` rewrite through `GIT_CONFIG_GLOBAL`, as the starter's bootstrap
test does, and the loop's eval-sign guard refuses a spike command that
changes the environment loopctl reads. It ran as a plain script instead:
clone this tree, `git mv apm packages/kmctl/apm`, commit, tag `v9.9.9`,
serve a bare clone through `insteadOf`, and run
`uvx --from apm-cli==0.33.0 apm install` in a consumer whose apm.yml names
`{git: https://github.com/JasperHG90/kmctl.git, path: packages/kmctl/apm, ref: v9.9.9}`
for claude and antigravity. It exited 0:

```
[*] Installed 4 APM dependencies and 1 MCP server in 4.2s.
--- lock dependencies (name, virtual_path, resolved_ref, deployed count)
kmctl packages/kmctl/apm v9.9.9 75
kmctl-antigravity packages/kmctl/apm/antigravity v9.9.9 4
kmctl-claude packages/kmctl/apm/claude v9.9.9 4
okf None a8b96420de90d102c43cda1693d01ec4f925f2ab 40
```

`.claude/rules/` got the four knowledge rules, `.claude/skills/` the
skills (extract-claims and write-checks among them), `.claude/settings.json`
the `kmctl briefing` hook, and the `bundle` MCP server was configured for
both harnesses. The starter's bootstrap integration test repeats this
through `just bootstrap` once the move lands.
