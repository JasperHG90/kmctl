---
type: eval
title: 'Eval: release-flow'
description: 'Definition of done for release-flow: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T09:50:09+00:00'
slug: release-flow
signoff:
  signer: human:jasperginn@gmail.com
  hash: b553e43272356aa2cf8cc702627c769a961ef1daf87574b0b5423a847dcdc82f
  at: '2026-10-16T09:50:09+00:00'
verified:
  by: human:jasperginn@gmail.com
  at: '2026-10-16T09:50:09+00:00'
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The plugin manifest is the one place the version is written: pyproject.toml's version is dynamic, read by hatchling's regex source from plugin/.claude-plugin/plugin.json, and a build of this branch is kmctl-0.1.0.
  Fails when: pyproject.toml still sets a fixed [project] version, the regex source does not name the manifest, or uv build of the repository gives a wheel or sdist whose version is not the manifest's
- r2: scripts/release.py reads the version (current), writes it (set), compares two versions (raised, same, lowered, skip for .dev or +local) and says whether one is a pre-release; set writes the manifest and points the five install lines in README.md, the tutorial and the how-to at @vX.Y.Z, from @main or an older tag, and never commits or tags.
  Fails when: current misreads the manifest, set leaves the manifest or any of the five doc lines unchanged, refuses an invalid version without a nonzero exit, compare gives a wrong verdict for any of the four cases, is-prerelease is wrong for a, b, rc or a final version, or set makes a commit or a tag
- r3: scripts/next_release_version.py gives the next version from the newest v* tag for PATCH, MINOR, MAJOR, PRE and FINAL, with --pre and --version, and needs --version when no tag exists.
  Fails when: any increment gives the wrong version in a real git repository under tmp_path, or with no v* tag it gives a version instead of refusing without --version
- r4: scripts/check_wheel.py refuses a wheel missing the plugin or the marketplace file, and scripts/smoke_wheel.py installs the wheel in a fresh venv and checks kmctl --version prints the release version and the installed package holds the plugin manifest.
  Fails when: check_wheel passes a wheel without kmctl/_plugin/ or kmctl/_marketplace.json, or smoke_wheel passes a wheel whose version differs from --version or that lacks the plugin manifest
- r5: release.yml is started by hand with increment, pre-release, version and dry run (default true), refuses a real run off main and an existing tag, runs the lint and test commands, builds and checks the wheel, and on a real run opens the version pull request on release/vX.Y.Z staging every file release.py set changed; release-tag.yml runs on a push to main touching the manifest, builds before it tags, and publishes a GitHub Release with the wheel, sdist and SHA256SUMS; neither publishes to PyPI; every action is pinned by a 40-character commit SHA; and only the jobs that write ask for write permissions.
  Fails when: a trigger, input or default differs, a step named above is missing, a job uploads to PyPI or uses a publish action, an action is pinned by tag or branch, the top-level permissions are not read-only, or the bump commit stages only the manifest
- r6: Decision 0012 records the release flow, the rejected hatch-vcs and PyPI, and the repository setting it needs; the architecture overview shows the release path; the how-to says how to upgrade to a release; and the bundle passes kmctl check.
  Fails when: the decision is missing, does not match kmctl schema decision, or does not name hatch-vcs, PyPI and the Actions pull-request setting; the overview does not mention release.yml and release-tag.yml; the how-to has no upgrade step; or kmctl check fails
- r7: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
