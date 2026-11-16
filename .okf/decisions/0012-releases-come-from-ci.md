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

The GitHub Release's notes come from `scripts/release_notes.py`, not
`gh release create --generate-notes`. GitHub's generated notes list merged
pull requests, and work lands on `main` as loop merges, so every release up
to v0.10.0 listed only its own version pull request. The script reads
`main`'s first-parent history since the tag before: each
`Merge loop/SLUG: SUMMARY` becomes a bullet under What changed, each other
commit one under Other changes, and loop state, release, branch-sync and
manual placeholder commits are left out. It fills the template
`.github/release-notes.md`, with the install lines for the tag and a compare
link, and `release-tag.yml` publishes the result with `--notes-file`.

## Correction, 2026-10-20

The 2026-10-19 correction says the release notes read only `main`'s
first-parent history and leave branch syncs out. Pull requests merged on
GitHub reach the local `main` through a sync such as
`Merge remote-tracking branch 'origin/main'`, so v0.12.0's notes listed none
of its six pull requests (issue #45). `scripts/release_notes.py` now also
reads the first-parent history each such sync brought in, except commits
that the release before or the history already read holds. Each
`Merge pull request #N` there, other than the release pull request, becomes
a What changed bullet with the title GitHub wrote in the merge's body, as
`TITLE (#N)`. A plain commit with the same text as a listed pull request's
title is left out, so a change committed to `main` and also merged as a pull
request shows once.

## Correction, 2026-11-11

The first release has landed. The workflows and `action.yml` now pin each
action to a commit SHA, and no `uses:` line names `@main`.

Found by the first `kmctl audit checks` run over the whole bundle
([ADR 0038](0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored.md)).

## Correction, 2026-11-14

The two workflows now release either package of the workspace
([ADR 0044](0044-kmctl-and-kmaudit-are-both-workspace-packages.md)).
`release.yml` takes a `package` input, `kmctl` or `kmaudit`. Each package has
its own version source and tag family: kmctl keeps `apm/apm.yml` and `vX.Y.Z`
tags, because users' `apm.yml` pins, `uses: JasperHG90/kmctl@vX` and copier's
`kmctl_ref` name them; kmaudit's version is the one line in
`packages/kmaudit/VERSION`, which its pyproject reads with hatchling's `regex`
source, and its tags are `kmaudit-vX.Y.Z`. The file starts at `0.1.0.dev0`,
which `scripts/release.py compare` skips, so adding it released nothing.
`next_release_version.py`, `release.py`, `check_wheel.py` and
`smoke_wheel.py` take `--package`.

The notes are now written before the release and reviewed with it. A notes
job, which runs in dry runs too, drafts them with
`scripts/release_notes.py --package P TAG --ref HEAD`, listing only commits
that touch the package's paths since its family's previous tag, as
`scripts/release_paths.py` decides them: kmaudit owns `packages/kmaudit/`,
kmctl owns `packages/kmctl/` and everything outside `packages/` but the
repository's bookkeeping (`.loop/`, `.okf/`, `.claude/`, `uv.lock`), which
ships in neither. release-tag asks the same script, so its warning and the
notes agree. The bump job commits the draft as
`.github/release-notes/TAG.md` in the version pull request, on top of the
exact commit it was drafted from, with a `Drafted-From: <sha>` trailer, and
puts the notes and the trailer in the pull request body. Merging approves
the notes too.

`release-tag.yml` runs on a change to `apm/apm.yml` or
`packages/kmaudit/VERSION`, once per package. It refuses before tagging when
`.github/release-notes/TAG.md` is missing or blank, and publishes that file
unchanged with `--notes-file`; it no longer runs `release_notes.py`. It warns,
in a `::warning::` and the step summary, about the package's commits that
landed between the drafted commit and the merge, so someone adds them with
`gh release edit`. It finds the drafted commit from the `Drafted-From`
trailer on the release branch's own commits, so an "Update branch" merge
from main on that branch does not hide the late commits. Only a kmctl release is marked Latest.

## Correction, 2026-11-15

kmaudit's command reference moved from `packages/kmaudit/docs/commands.md`
to `docs/reference/kmaudit-commands.md`, beside kmctl's, so the repository
keeps one `docs/`. `scripts/release_paths.py` now gives kmaudit its pages in
`docs/` too: those whose file names start with `kmaudit-`. kmctl owns every
other path outside `packages/`, as before. `release.py set --package kmaudit`
pins the tracing install line in the moved page, and `release.py set` pins
kmctl's CLI install line in `packages/kmctl/README.md`, since the root
`README.md` is now a short map with no install line.

## Correction, 2026-11-16

The 2026-11-14 correction names `apm/apm.yml` as kmctl's version source,
`packages/kmaudit/VERSION` as kmaudit's, and those two files as what
`release-tag.yml` watches. Since
[ADR 0045](0045-each-package-keeps-its-apm-package-and-version.md) each
package keeps its APM package and its version in its own folder: kmctl's
version is the `version:` line of `packages/kmctl/apm/apm.yml`, kmaudit's
the `version:` line of `packages/kmaudit/apm/apm.yml`, and the VERSION file
is gone. `release-tag.yml` runs on a change to
`packages/kmctl/apm/apm.yml` or `packages/kmaudit/apm/apm.yml`, once per
package. The tag families are unchanged.
