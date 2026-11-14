---
type: decision
title: "ADR 0044: kmctl and kmaudit are both workspace packages"
description: "kmctl moves from the repository root to packages/kmctl beside kmaudit, the root becomes a uv workspace that installs nothing, and releases after v0.12.1 install from #subdirectory=packages/kmctl."
tags: [decision]
generated:
  by: process:kmctl/0.12.1
  at: 2026-11-14T20:22:53Z
status: stable
sources:
  - resource: "pyproject.toml"
  - resource: "packages/kmctl/pyproject.toml"
  - resource: "packages/kmctl/hatch_build.py"
  - resource: "packages/kmctl/src/kmctl/pin.py"
  - resource: ".pre-commit-hooks.yaml"
---

# ADR 0044: kmctl and kmaudit are both workspace packages

## Context

ADR 0043 moved the audit into `packages/kmaudit/` and kept kmctl at the
repository root, so its install URLs, the GitHub Action and the release
flow would not move. That left the root as two things at once: the uv
workspace and the kmctl package. On 2026-11-14 the operator asked for the
layout of his uv-monorepo template instead, with every library under
`packages/`, so the release and CI work that follows can treat kmctl and
kmaudit the same way.

## Decision

kmctl moves to `packages/kmctl/`: its own `pyproject.toml`, `src/kmctl/`
and the tests whose subject is the package. The root `pyproject.toml` is a
workspace root that installs nothing: `[tool.uv] package = false`, members
`packages/*`, each member a `{ workspace = true }` source and in the `dev`
group, and the shared ruff and pytest config. One `uv.lock` stays at the
root, and `uv run pytest` there still runs `tests/`, `packages/kmctl/tests/`
and `packages/kmaudit/tests/`. Tests of repository files (the workflows,
the release scripts, the rules and skills) stay in the root `tests/`.

The version still comes from `apm/apm.yml` (ADR 0012), now two folders up.
`packages/kmctl/hatch_build.py` puts `apm/`'s skills, agents and rules in
the wheel: from `../../apm` in a checkout, and from the sdist's own copy of
those folders when a wheel is built from the sdist. `scripts/check_wheel.py`
reads that hook's table.

Releases after v0.12.1 install from
`git+https://github.com/JasperHG90/kmctl@vX.Y.Z#subdirectory=packages/kmctl`.
`scripts/release.py set` writes the fragment on every install line and
hook hint. The pin hand-off (ADR 0026) and the starter's `kmctl_src` add it
only for refs newer than v0.12.1, since older tags build from the root.
The action installs `packages/kmctl` from its own checkout. The
`kmctl-check` pre-commit hook installs `./packages/kmctl` as an extra
dependency; pre-commit and prek install the hook repository's root first,
so the root has a hatchling build that makes an empty wheel. uv never
builds it.

Rejected:

- Keeping kmctl at the root (ADR 0043): the root stays both workspace and
  package, unlike the template and unlike kmaudit.
- A committed `packages/kmctl/apm` symlink to `../../apm`: it built every
  way on Linux, but a Windows checkout without `core.symlinks` turns it
  into a text file.
- Building only wheels: the release would stop shipping an sdist.

## Consequences

- A kmctl at v0.12.1 or older on someone's PATH cannot hand off to a
  project pinned to a later release, because it asks uvx for the root. They
  install a newer CLI first; the starter's `just kmctl` already installs one
  as new as the pin.
- Until the next release, the install lines on main name v0.12.1 with the
  fragment, which that tag cannot build; `scripts/release.py set` points
  them at the new tag in the version pull request.
- Paths that named the root moved with the package: the source-tree
  fallbacks to `apm/` in `plugin.py`, `antigravity.py` and `opencode.py`,
  `uv build --package kmctl` in both release workflows, and the starter
  job's test path in `ci.yml`.
