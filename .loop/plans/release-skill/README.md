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
4. **After the merge, watch release-tag and check what it published.** Find
   the release-tag run for the merge commit (`gh run list --workflow
   release-tag.yml`), follow it with `gh run watch`, and read its log and step
   summary with `gh run view`. When commits landed on main between the draft
   and the merge, release-tag still publishes the reviewed file unchanged, but
   writes a `::warning::` and a step-summary section naming those late commits
   (`release-per-package`). `gh release view TAG` cannot show them, because by
   construction they are missing from the notes. Then read the published notes
   with `gh release view TAG`.
5. **Close a gap without throwing away the reviewed text.** Under D3 the
   published notes are the reviewed file: the Hermes rewrite plus any edits
   made in the pull request. So when a late commit or any other change the
   release holds is missing:
   - add the missing entry by hand to the published notes, keeping the rest of
     the reviewed text, and set them with `gh release edit TAG --notes-file
     FILE`;
   - make the same edit to the committed notes file
     .github/release-notes/TAG.md (written by release-per-package) in a follow-up commit, so the repo and
     the Release say the same thing;
   - when the draft missed a change it should have listed (not a late commit),
     also fix `scripts/release_notes.py` so future drafts get it right.

   Never regenerate published notes from the script. That would replace the
   reviewed prose with the raw draft and leave the committed file saying
   something else.

The skill follows `.claude/rules/skills-are-thin.md` in spirit: it picks the
inputs only the operator can choose (package, increment, pre-release), runs
the commands, and quotes their output. It does not restate what the workflows
enforce.

`.claude/rules/releases.md` gets shorter. It keeps the two rules that must
load in every session, even when nobody runs the skill: never merge the
version pull request with `--admin`, and `every-release-has-notes` (reworded
for D3: the notes are reviewed in the pull request; after the merge, read
release-tag's late-commit warning and `gh release view TAG`; a gap found then
is added by hand to both the published Release and the committed
.github/release-notes/TAG.md (written by release-per-package), keeping the reviewed text, and
`scripts/release_notes.py` is fixed when the draft missed a change; published
notes are never regenerated). The prose about the flow moves into the
skill, and the rule points to it. A rule loads every session; a skill loads
only when someone releases. So the constraints stay in the rule and the steps
go in the skill.

A new test, `new:tests/test_release_skill.py`, pins the skill to the repo so
it cannot drift. `tests/test_skills.py` covers only `apm/.apm/skills`, and no
test reads `.claude/skills/` today. The new test checks that:

- every `-f KEY=` in the skill names an input of `release.yml`;
- the package names the skill offers match that input's options;
- every repo path the skill cites in backticks exists, where a path holding a
  `<tag>` or `<package>` placeholder counts as a glob and must match at least
  the folder before the placeholder;
- the skill explains why `release.yml` and `release-tag.yml` both exist and
  why `apm/apm.yml` is kmctl's version source (tests named so
  `-k explains` selects them);
- the after-merge step names watching the release-tag run (`gh run watch` or
  `gh run view`) and its late-commit warning, and the gap step names both
  `gh release edit` and the committed notes file and does not tell the reader
  to regenerate published notes;
- `releases.md` points at the skill and its reworded
  `every-release-has-notes` carries the same no-regenerate fix (tests named
  so `-k rule` selects them).

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

- P1: No skill walks a release: the flow lives as prose in `.claude/rules/releases.md`, assumes one package, never says why `release.yml` and `release-tag.yml` are separate or why `apm/apm.yml` is kmctl's version source, and nothing reads release-tag's run for late commits missing from the notes
- P2: `.claude/rules/releases.md` will describe a stale one-package flow once releases take a package and the notes are committed in the version pull request, its after-publish fix (regenerate the notes from the script) would overwrite the reviewed notes, and it would repeat the skill's steps
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
- checked by: `new:tests/test_release_skill.py` (front matter names `release`; every `-f KEY=` is a `release.yml` input; package values match the input's options; cited paths exist, `<tag>`/`<package>` placeholders matched as globs; `-k explains` tests for the two-workflow and version-source explanations; the after-merge step watches the release-tag run with `gh run watch`/`gh run view` and reads its `::warning::`/step summary of late commits; the gap step edits both the Release and the committed notes file and never regenerates), and a manual `/release kmaudit` dry run
- seen by: operator

### O2: `releases.md` keeps only the no-`--admin` rule and `every-release-has-notes`, reworded so notes are reviewed in the pull request and a gap after publish is added by hand to the Release and the committed notes file, never regenerated, and points at the skill
- kind: support
- goal: G2
- fixes: P2
- needs: O1
- touches: `.claude/rules/releases.md`
- checked by: `tests/test_rules.py` (cited paths exist, cited ADRs exist) and `new:tests/test_release_skill.py` `-k rule` (the rule names the skill's folder `.claude/skills/release/`, names `gh release edit` and the committed notes file, and does not say to regenerate published notes)
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
