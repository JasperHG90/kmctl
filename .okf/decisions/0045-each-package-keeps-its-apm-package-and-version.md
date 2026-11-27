---
type: decision
title: "ADR 0045: Each package keeps its APM package and version"
description: "kmctl's APM package moves from apm/ to packages/kmctl/apm, kmaudit gets one in packages/kmaudit/apm whose apm.yml carries its version in place of a VERSION file, and releases after v0.12.2 are added with path: packages/kmctl/apm."
tags: [decision]
generated:
  by: process:kmctl/0.12.2
  at: 2026-11-15T06:53:06Z
status: stable
sources:
  - resource: "packages/kmctl/apm/apm.yml"
  - resource: "packages/kmaudit/apm/apm.yml"
  - resource: "packages/kmctl/src/kmctl/plugin.py"
  - resource: "packages/kmctl/src/kmctl/doctor.py"
  - resource: "scripts/release.py"
  - resource: "starter/apm.yml.jinja"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0045: Each package keeps its APM package and version

## Context

ADR 0012 keeps a package's version in its APM package's `apm.yml`. After
ADR 0044, kmctl's code sat in `packages/kmctl/` but its APM package stayed
at the repository root in `apm/`, read from two folders up, and kmaudit had
no APM package, so release-per-package gave it a one-line
`packages/kmaudit/VERSION` instead. On 2026-11-15 the operator said that a
VERSION file "is not how we do version management", and that if kmaudit
gets an APM package in its folder, kmctl's should move into its own.

## Decision

kmctl's APM package moves from `apm/` to `packages/kmctl/apm/` with
`git mv`, so its skills, agents, rules, hooks and the `claude` and
`antigravity` sub-packages keep their history. kmaudit gets an APM package
in `packages/kmaudit/apm/` whose `apm.yml` carries its version, replacing
`packages/kmaudit/VERSION`; for now it holds only the name, version and
description. Each package's `[tool.hatch.version]` and uv `cache-keys` read
`apm/apm.yml` inside the package folder with the same regex, and kmctl's
build hook, sdist and `scripts/check_wheel.py` read `apm/` there too, with
no path out of the package. The root `apm.yml`, this repository's own
install of its dependencies, stays at the root.

`scripts/release.py` reads and writes each package's `apm.yml`.
`release-tag.yml` triggers on either one, and its read of the commit before
the push falls back to `apm/apm.yml`, because the first release after the
move compares against a commit from before it.

Both moves, kmctl's code (ADR 0044) and this one, ship in the first
release after `LAST_ROOT_RELEASE` (v0.12.2). A consumer adds a later
release as `{git: https://github.com/JasperHG90/kmctl.git, path: packages/kmctl/apm, ref: vX.Y.Z}`
and keeps `path: apm` for v0.12.2 and older. APM records the package and
its sub-packages under the virtual paths `packages/kmctl/apm`,
`packages/kmctl/apm/claude` and `packages/kmctl/apm/antigravity`.
`kmctl.plugin.new_entry()` writes the path for this CLI's release, and
`kmctl.plugin` and `kmctl.doctor` recognise kmctl's entry and its
sub-packages under either path. Every fix that moves a project to this
CLI's release gives the whole entry, path and ref, because a move across
the cutoff changes both: doctor's update fix, `kmctl plugin patch`'s
refusals and the install how-tos. The starter's `apm.yml` picks the path
from `kmctl_ref` the way its justfile picks `kmctl_src`. The tag test of
ADR 0044 grows to hold the cutoff for both moves: a tag after it has
`packages/kmctl/apm/apm.yml` and no `apm/apm.yml`, an older one the
reverse.

Rejected:

- Keeping `packages/kmaudit/VERSION`: it breaks the convention of
  ADR 0012, and kmaudit's skills and agents need an APM package anyway.
- Leaving kmctl's package at the root and adding one for kmaudit: the two
  packages would keep their APM packages in different places.
- A symlink at either path: ADR 0044 already rejected one, because a
  Windows checkout without `core.symlinks` turns it into a text file.

## Consequences

- A project pinned to v0.12.2 or older keeps working with `path: apm`.
  Moving it to a later release changes the path as well as the ref;
  doctor's fix and the docs say so, and `apm uninstall` takes the name
  ending with the entry's path.
- A root release made on main before this layout merges moves the cutoff
  for both moves; the tag test fails until it does.
- This amends ADR 0044, whose version source and build hook read
  `../../apm`.
