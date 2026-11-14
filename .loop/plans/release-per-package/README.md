---
type: plan
title: 'Plan: release-per-package'
description: Release kmctl or kmaudit from one Release run, each with its own version source, tag family and path-filtered notes committed in the version pull request.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:22:54+00:00'
slug: release-per-package
epic: monorepo-release
depends_on:
- kmctl-to-packages
priority: null
schema_version: '2.0'
---

# release-per-package

Relayed from: none

## Intent

The Release workflow (`.github/workflows/release.yml`) takes `package: kmctl|kmaudit`
and releases either package; `.github/workflows/release-tag.yml` tags and publishes
whichever package's version went up. This is decision D2 of epic `monorepo-release`
and the deterministic half of D3. Decisions recorded here, not reopened:

- D2: kmctl keeps `vX.Y.Z` tags, because users' `apm.yml` pins, `uses: JasperHG90/kmctl@vX`
  and copier's `kmctl_ref` depend on them. kmaudit gets `kmaudit-vX.Y.Z`. Each
  package's notes cover only commits that touch that package's paths since that
  family's previous tag.
- D3 (deterministic half): the Release run drafts the notes with
  `scripts/release_notes.py`, commits them as .github/release-notes/TAG.md (folder
  created by this ticket) in the version pull request, and puts them in the pull
  request body. Merging approves the notes too. release-tag publishes that file and
  refuses when it is missing or empty. The Hermes rewrite is ticket
  `release-notes-hermes`, which replaces the draft file between the draft step and
  the pull-request step; this ticket makes that seam.
- Layout from `kmctl-to-packages` (D1): the root `pyproject.toml` becomes a virtual
  uv workspace root (`[tool.uv] package = false`, members `packages/*`), each package
  has its own full pyproject, and one root `uv.lock`. kmctl lives in `packages/kmctl`.

Version sources:

- kmctl: `apm/apm.yml`, as now (ADR 0012, ADR 0014). Users pin the APM package to
  the CLI's tag, so the two must share one version.
- kmaudit: a new one-line file `new:packages/kmaudit/VERSION`, read by hatchling's
  `regex` version source, with `version` made dynamic in
  `packages/kmaudit/pyproject.toml`. Why not the static `version = "0.1.0"` it has
  today: `uv.lock` copies a static workspace member's version (kmaudit's entry
  says `version = "0.1.0"`; kmctl's dynamic entry has no version line), so every
  kmaudit bump would also have to re-lock and stage `uv.lock`, and release-tag's
  path trigger would fire on every dependency edit to the pyproject. A dynamic
  regex source is the shape kmctl already uses, which spike `spike:release-flow/1`
  showed gives the right version for a build, a git install at a tag and an
  install from an archive. A `[tool.uv] cache-keys` entry for the file keeps a
  local `uv run` rebuilding on a bump, as the root does for `apm/apm.yml` today.

Which paths belong to which package, for the notes: kmaudit owns `packages/kmaudit/`.
kmctl owns `packages/kmctl/` and every path outside `packages/` (the action, `apm/`,
the starter, docs, `.okf/`, scripts, workflows), because the `v*` tag is what ships
them. A commit counts for a package when its diff against its first parent touches
one of its paths; loop state and release commits stay skipped as today. Measured on
`agent-audit`: of the 16 first-parent commits since `v0.12.1` that are not loop or
release commits, 13 touch only kmctl's paths, 3 touch both (root tooling plus
kmaudit), and 0 touch only kmaudit, so today a kmaudit release would list 3
bullets and kmctl 16, where the unfiltered script would list all 16 in both.

Late commits: a commit that lands on main after the Release run drafts the notes and before the version pull request merges ships in the tag without a bullet, and the next release's notes start after it. The draft records the commit it was drafted from in an HTML comment; release-tag lists the package's commits between that commit and the merge, and when there are any it still publishes exactly the reviewed file but writes a `::warning::` and a step-summary section naming them, so someone adds them with `gh release edit`. Release-tag never rewrites the reviewed notes itself (D3).

Only a kmctl release is marked Latest (`--latest`); a kmaudit release passes
`--latest=false`. The untracked root `release.yml` and `plugin-tag.yml` are shape
references only and are never committed.

The outcome that shows it worked: `tests/scripts/test_workflows.py` pins a Release
run with a `package` input whose real run commits .github/release-notes/kmaudit-vX.Y.Z.md
(or vX.Y.Z.md) and builds the pull request body from that file, and a
release-tag that, for each package whose version source rose, builds that package,
refuses before tagging when the committed notes file is missing or empty, and
publishes the file as the Release body, Latest only for kmctl.

## Problems

- P1: `scripts/next_release_version.py`, `scripts/release.py`, `scripts/check_wheel.py` and `scripts/smoke_wheel.py` know only kmctl: one `v*` tag family, one version source and kmctl's wheel checks, so nothing can work out, set or check a kmaudit release
- P2: kmaudit's version is a static literal in `packages/kmaudit/pyproject.toml` that `uv.lock` copies, so a bump edits two files and its trigger fires on every dependency edit
- P3: `scripts/release_notes.py` lists every commit since the previous `v*` tag whatever it touched, and refuses a tag that is not pushed yet, so it cannot draft one package's notes before the release
- P4: the Release run takes no package, writes no notes, and opens a version pull request whose body says nothing about what changed, so nobody reviews the notes before they ship
- P5: `.github/workflows/release-tag.yml` watches only `apm/apm.yml`, builds only kmctl, generates its own notes at publish time without refusing empty ones, and lets every Release become Latest

## Goals

- G1: Either package can be released from the same two workflows, each with its own version source and tag family, and only kmctl's release is Latest
- G2: Every release publishes the notes that were reviewed in its version pull request, listing only that package's commits since its family's previous tag

## Outcomes

### O1: kmaudit's version comes from a one-line VERSION file that hatchling reads
- kind: support
- goal: G1
- fixes: P2
- needs: none
- touches: `new:packages/kmaudit/VERSION`, `packages/kmaudit/pyproject.toml`, `uv.lock`
- checked by: a test that `scripts/release.py --package kmaudit current` prints the VERSION file's value and the pyproject declares version dynamic with a regex source on that file; `uv lock --check` passes with no kmaudit version line
- seen by: nobody

### O2: The version and wheel scripts take `--package kmctl|kmaudit`
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `scripts/next_release_version.py`, `scripts/release.py`, `scripts/check_wheel.py`, `scripts/smoke_wheel.py`, `tests/scripts/test_next_release_version.py`, `tests/scripts/test_release.py`, `tests/scripts/test_check_wheel.py`, `tests/scripts/test_smoke_wheel.py`
- checked by: tests that next_release_version reads only `kmaudit-v*` tags for kmaudit and only `v*` for kmctl, that `release.py set --package kmaudit` writes only the VERSION file and pins the install line in `packages/kmaudit/README.md` to `kmaudit-vX.Y.Z`, that kmctl's `set`, `current` and `manifest` behave as today, that a new `release.py tag` verb prints the tag for a package and version, and that the smoke test runs `kmaudit --version` with no skills check for kmaudit
- seen by: calling code

### O3: release_notes.py drafts one package's notes for a tag not yet pushed, into a file
- kind: support
- goal: G2
- fixes: P3
- needs: O2
- touches: `scripts/release_notes.py`, `.github/release-notes.md`, `new:.github/release-notes-kmaudit.md`, `tests/scripts/test_release_notes.py`
- checked by: tests on a scratch git repo that `release_notes.py --package kmaudit kmaudit-v0.2.0 --ref HEAD --out FILE` writes notes for the range from the family's previous tag to HEAD when the tag does not exist, lists a commit touching `packages/kmaudit/` but not one touching only kmctl's paths (and the reverse for kmctl), never counts a `v*` tag as kmaudit's previous tag, skips `release/kmaudit-v` merges and `release: kmaudit-v` commits, and fills the kmaudit template's install line with `#subdirectory=packages/kmaudit`; existing tagged-tag tests still pass
- seen by: calling code

### O4: The Release run takes a package, drafts its notes to a file, and commits that file into the version pull request and its body
- kind: behaviour
- goal: G2
- fixes: P4
- needs: O2, O3
- touches: `.github/workflows/release.yml`, `tests/scripts/test_workflows.py`
- checked by: workflow tests that the inputs are `package` (choice kmctl, kmaudit), increment, prerelease, version and dry_run; that resolve passes `--package` and checks the family's tag on origin; that build runs `uv build --package` for the chosen package and the per-package wheel checks; that a draft step writes `release_notes.py` output to the notes file path before the bump step, as its own step a later step can replace; that bump opens `release/TAG`, stages the notes file with every file `release.py set` wrote, and passes the same file to `gh pr create --body-file`; and that a dry run still drafts the notes and shows them in the step summary
- seen by: operator

### O5: release-tag publishes the committed notes for whichever package's version rose, refuses without them, and marks only kmctl Latest
- kind: behaviour
- goal: G1
- fixes: P5
- needs: O2, O4
- touches: `.github/workflows/release-tag.yml`, `tests/scripts/test_workflows.py`, `.okf/decisions/0012-releases-come-from-ci.md`, `.okf/architecture/overview.md`
- checked by: workflow tests that the push paths are `apm/apm.yml` and `packages/kmaudit/VERSION`; that the tag job runs once per package (matrix) comparing that package's version before and after; that the step refusing a missing or blank .github/release-notes/TAG.md runs before `git tag -a`; that `gh release create` uses `--notes-file` on that committed file with no call to `release_notes.py` and no `--generate-notes`; that kmctl passes `--latest` and kmaudit `--latest=false`; and that ADR 0012 carries a dated Correction naming the package input, the tag families, the VERSION file and the committed notes file, checked by `tests/scripts/test_release_docs.py`
- seen by: operator

## Could invalidate this plan

- After `kmctl-to-packages` moves kmctl's pyproject into `packages/kmctl`, its hatchling `regex` version source may be unable to read `apm/apm.yml` outside the package folder (or the sdist may not carry it), which would force kmctl's version source somewhere else and change what `release.py`, the Release run and release-tag's trigger read. `kmctl-to-packages` owns that choice; this plan assumes `apm/apm.yml` stays kmctl's one version source as D2 and D5 say. spike:kmctl-to-packages/3 settles it: with kmctl's moved pyproject reading apm.yml two folders up and a hatch build hook for the force-includes, the sdist build, the wheel build, the git-subdirectory install and the folder install all report apm.yml's version (the sdist reads it from PKG-INFO), so apm/apm.yml stays kmctl's one version source.
