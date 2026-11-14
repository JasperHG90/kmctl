---
type: plan
title: 'Plan: release-skill'
description: A repo-local release skill that takes the package name and walks the dry run, the real run, the notes review in the version pull request and the check of the published notes.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:21:01+00:00'
slug: release-skill
epic: monorepo-release
depends_on:
- release-per-package
- release-notes-hermes
priority: null
schema_version: '2.0'
---

# release-skill

Relayed from: none

## Intent

Add a repo-local skill, `new:.claude/skills/release/` holding one SKILL.md, that an
operator or agent runs as `/release kmctl` or `/release kmaudit` (decision D5
of the `monorepo-release` epic). It sequences one release from start to
finish and keeps the "why" next to the steps:

1. **Why two workflows.** `.github/workflows/release.yml` is run by hand. It
   works out the version, lints, tests, builds, generates the notes (draft
   from `scripts/release_notes.py`, rewritten by Hermes, draft kept if Hermes
   fails), and opens the version pull request with the notes file committed in
   it. Merging that pull request approves the version and the notes. The merge
   happens after the first run has ended, so a second workflow,
   `.github/workflows/release-tag.yml`, fires on the push to `main`, tags the
   merge commit and publishes the GitHub Release from the committed notes
   file. It refuses when that file is missing or empty. release-tag is not
   "for APM", but it watches `apm/apm.yml` because that file is kmctl's
   version source: users pin the APM package with `ref: v<cli version>`
   (`.claude/rules/cli-version-floor.md`), so the manifest and the CLI must
   carry the same version and the same `vX.Y.Z` tag. kmaudit has its own
   version source and its own `kmaudit-vX.Y.Z` tag family (D2).
2. **Dry run, then the real run**, each through
   `gh workflow run release.yml -f package=<name> ...` and `gh run watch`.
   The skill passes only the inputs `release.yml` declares.
3. **Review the notes in the version pull request**: read the notes file and
   the pull request body. When the notes miss a change or read badly, edit the
   file on the release branch. Never merge with `--admin`. The bot-opened pull
   request runs no checks until it is closed and reopened.
4. **After publish**, read `gh release view TAG`. When the notes leave out a
   change the release holds, fix `scripts/release_notes.py`, not the notes,
   and set the regenerated notes with `gh release edit` (the existing
   `every-release-has-notes` constraint).

The skill follows `.claude/rules/skills-are-thin.md` in spirit: it picks the
inputs only the operator can choose (package, increment, pre-release), runs
the commands, and quotes their output. It does not restate what the workflows
enforce.

`.claude/rules/releases.md` gets shorter. It keeps the two rules that must
load in every session, even when nobody runs the skill: never merge the
version pull request with `--admin`, and `every-release-has-notes` (reworded
for D3: the notes are reviewed in the pull request, and a gap found after
publish is fixed in the script). The prose about the flow moves into the
skill, and the rule points to it. A rule loads every session; a skill loads
only when someone releases. So the constraints stay in the rule and the steps
go in the skill.

A new test, `new:tests/test_release_skill.py`, pins the skill to the repo so
it cannot drift. `tests/test_skills.py` covers only `apm/.apm/skills`, and no
test reads `.claude/skills/` today. The new test checks that:

- every `-f KEY=` in the skill names an input of `release.yml`;
- the package names the skill offers match that input's options;
- every repo path the skill cites in backticks exists;
- `releases.md` points at the skill.

`tests/test_rules.py` already checks the paths that `releases.md` cites.

**Measurement.** Over git history and `gh release list` there have been 16
kmctl releases, v0.2.0 to v0.12.2, and 0 kmaudit releases. All 16 went
through the flow `releases.md` describes in prose, and nothing walks it step
by step. The skill fires on every release: 16 of 16 so far, and every future
release of both packages. Its after-publish step is the check that caught
v0.12.0's notes leaving out six pull requests, as `releases.md` records. Once
`release-per-package` and `release-notes-hermes` land, its review step moves
that check to before publish.

The outcome that shows it worked: running `/release kmaudit` in a session
leads to a dry run and then a real run of `release.yml` with
`package=kmaudit`. The new test passes, and `tests/test_rules.py` still
passes on the shorter `releases.md`.

## Problems

- P1: No skill walks a release: the flow lives as prose in `.claude/rules/releases.md`, assumes one package, and never says why `release.yml` and `release-tag.yml` are separate or why `apm/apm.yml` is kmctl's version source
- P2: `.claude/rules/releases.md` will describe a stale one-package flow once releases take a package and the notes are committed in the version pull request, and it would repeat the skill's steps
- P3: No test reads `.claude/skills/`, so a repo-local skill that names a renamed workflow input or a moved file goes stale silently

## Goals

- G1: An operator or agent releases kmctl or kmaudit by naming the package, and every release goes out with notes that were reviewed before merge and checked after publish
- G2: The always-loaded release rule and the skill do not repeat each other, and the skill stays true to the workflows it drives

## Outcomes

### O1: `/release <kmctl|kmaudit>` walks the dry run, the real run, the notes review in the version pull request and the published-notes check
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:.claude/skills/release/`
- checked by: `new:tests/test_release_skill.py` (front matter names `release`, every `-f KEY=` is a `release.yml` input, package values match the input's options, cited paths exist), and a manual `/release kmaudit` dry run
- seen by: operator

### O2: `releases.md` keeps only the no-`--admin` rule and `every-release-has-notes`, reworded for notes reviewed in the pull request, and points at the skill
- kind: support
- goal: G2
- fixes: P2
- needs: O1
- touches: `.claude/rules/releases.md`
- checked by: `tests/test_rules.py` (cited paths exist, cited ADRs exist) and `new:tests/test_release_skill.py` (the rule names the skill's folder `.claude/skills/release/`)
- seen by: operator

### O3: A test pins the repo-local release skill to `release.yml`'s inputs and the files it cites
- kind: support
- goal: G2
- fixes: P3
- needs: O1
- touches: `new:tests/test_release_skill.py`
- checked by: the test fails on a copy of the skill with a made-up `-f` input or a missing path, and passes on the real one
- seen by: nobody

## Could invalidate this plan

- none
