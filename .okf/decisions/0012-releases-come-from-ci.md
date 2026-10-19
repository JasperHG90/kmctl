---
type: decision
title: "ADR 0012: Releases come from CI"
description: "A hand-run release workflow opens a version pull request and a tag workflow publishes the GitHub Release; the plugin manifest is the one version source, with no PyPI and no hatch-vcs."
tags: [adr, decision, release]
generated:
  by: claude-opus/5.5
  at: 2026-10-16T10:00:25Z
status: stable
---

# ADR 0012: Releases come from CI

- Status: Accepted
- Date: 2026-10-16

## Context

kmctl had no releases. On 2026-10-16 the repository had 0 `v*` tags and 0
GitHub Releases over 1173 commits on `main`. The version was written twice by
hand, `0.1.0` in `pyproject.toml` and in `plugin/.claude-plugin/plugin.json`,
nothing built or checked a release, and every install line in the docs
followed `main`, so a user could not pin the kmctl they had tested.

The plugin ships inside the wheel ([ADR 0001](0001-standalone-cli-installs-its-plugin.md)),
and `kmctl plugin install` stamps the CLI's version into the plugin it stages,
so one version names both. kmctl installs three ways: `uv tool install` from
git at a tag, `uv build`, and `action.yml`, which runs `uv tool install` on the
action's own checkout. GitHub hands an action to a workflow as a download with
no `.git` folder.

## Decision

The plugin manifest, `plugin/.claude-plugin/plugin.json`, is the one place the
version is written. `pyproject.toml` declares the version dynamic and reads it
with hatchling's `regex` version source, so every build, with or without git
history, carries the manifest's version (loop spike `release-flow/1` built a
wheel, an sdist, a git install at a tag and an install from a `git archive`
folder, and all printed the manifest's version).

Two workflows make a release, each command a step of its own:

- `.github/workflows/release.yml`, run by hand, works out the version from the
  newest `v*` tag (`scripts/next_release_version.py`), refuses a real run off
  `main` or a tag that exists, runs the lint and the tests, and builds and
  checks the wheel at that version (`twine check`, `scripts/check_wheel.py`,
  `scripts/smoke_wheel.py`). A dry run, the default, stops there. A real run
  commits `scripts/release.py set` (the manifest, and the five install lines
  in the docs pinned to the new tag) on `release/vX.Y.Z` and opens the version
  pull request. Merging it is the approval.
- `.github/workflows/release-tag.yml` runs when a push to `main` changes the
  manifest. When the version went up, it builds and checks the release files
  first, then pushes the annotated tag `vX.Y.Z` and publishes a GitHub Release
  with the wheel, the sdist and `SHA256SUMS`.

Rejected: hatch-vcs, which reads the version from the git tag. `action.yml`
installs kmctl from a download with no `.git`, where hatch-vcs has no tag to
read and falls back to a placeholder version, so the action would report the
wrong kmctl.

Rejected: publishing to PyPI. The operator chose GitHub Releases only; users
install from git at a tag, and the Release holds the files for anyone who
wants them.

## Consequences

- `kmctl --version`, the plugin stamp and the action all report the manifest's
  version, and a version change is a one-line diff that `release-tag.yml`
  acts on.
- The bump job opens its pull request with `GITHUB_TOKEN`, which needs the
  repository setting
  "Allow GitHub Actions to create and approve pull requests"
  (Settings, Actions, General). It was off; the operator turned it
  on on 2026-10-16 instead of adding a token secret. If it is turned off, the
  bump job deletes its branch and fails, naming the setting.
- A pull request opened with `GITHUB_TOKEN` starts no workflow, so the version
  pull request shows no checks; `release.yml` runs the lint and the tests
  itself before it opens one.
- The first release needs `--version`, since no tag exists to count from.
  Until it lands, the docs' `uv tool install` lines name no ref and the
  action's `uses:` lines name `@main`.
- A hand edit to the manifest's version on `main` also releases, through the
  same build-and-check steps.

## Correction, 2026-10-16

The one version source is now `apm/apm.yml`, kmctl's APM package, not the
plugin manifest, which is gone with `plugin/`
([ADR 0014](0014-apm-is-the-only-install-route.md)). `pyproject.toml`'s
hatchling `regex` source reads its `version:` line, `scripts/release.py set`
writes it and copies it to the root `apm.yml`, `current` refuses when the two
differ, and `release.yml` and `release-tag.yml` stage and watch `apm/apm.yml`
instead of the manifest. The rest of the release flow is unchanged.

## Correction, 2026-10-17

The docs hold six install lines for `scripts/release.py set` to point at
the release tag, not five: the CI how-to's audit workflow now has a second
job, which uses the action in `mode: publish`
([ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)).

## Correction, 2026-10-19

The 2026-10-16 correction says `scripts/release.py set` copies the version
to the root `apm.yml` and that `current` refuses when the two differ. `set`
writes it into four apm.yml files (`APM_FILES`): the root `apm.yml`,
`apm/apm.yml`, and the two per-harness sub-packages `apm/claude/apm.yml`
and `apm/antigravity/apm.yml`
([ADR 0020](0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md)),
because APM needs a `version:` in each. `current` refuses when any of them
differs from `apm/apm.yml`. `set` also pins the install line in
`docs/how-to/install-kmctl-with-apm.md` and moves the `kmctl_ref` default in
`copier.yml` to `v<version>`, so the starter template a release tag carries
pins that release
([ADR 0025](0025-the-starter-template-lives-in-kmctl-and-shares-its-release-tags.md)).
`apm/apm.yml` is still the one version source.
