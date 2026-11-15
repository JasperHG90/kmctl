---
name: release
description: Release kmctl or kmaudit through CI - a dry run of the Release workflow, the real run, a review of the notes in the version pull request, then a check of what release-tag published and a fix by hand for any change the notes leave out. Use when asked to release, cut, ship or publish a version of kmctl or kmaudit, or to fix a published release's notes.
argument-hint: "<kmctl|kmaudit>"
---

# Release a package

Run as `/release kmctl` or `/release kmaudit`. The argument is the package.
With no argument, ask which one. The constraints that hold even without this
skill live in `.claude/rules/releases.md`; this skill holds the steps.

## Why two workflows

`.github/workflows/release.yml` runs by hand. It works out the version, lints,
tests and builds, drafts the notes with `scripts/release_notes.py`, has Hermes
rewrite them for users (the draft stands when the rewrite fails its checks),
and opens the version pull request. That pull request commits the new version
and the notes as `.github/release-notes/<tag>.md`, with the notes as its body.

Merging the pull request approves the version and the notes. The merge
happens after the Release run has ended, so nothing in that run can tag the
merge commit. `.github/workflows/release-tag.yml` does it: it fires on the
push to main that changes a version source, tags the merge commit, and
publishes the GitHub Release with the committed notes file as its body,
unchanged. It refuses when that file is missing or blank, so no release goes
out without notes.

release-tag is not an APM workflow, but APM is why kmctl's tags matter. Users
pin kmctl's APM package with `ref: v<cli version>`
(`.claude/rules/cli-version-floor.md`), the GitHub Action by its tag, and the
starter template by the `kmctl_ref` default in `copier.yml`. So the package
and the CLI must carry one version and one tag: `packages/kmctl/apm/apm.yml`
is kmctl's version source, and release-tag tags it `vX.Y.Z`. kmaudit has its
own version source, its APM package's `packages/kmaudit/apm/apm.yml`, and its
own `kmaudit-vX.Y.Z` tags (ADR 0045). Only a
kmctl release becomes Latest.

## Inputs

Settle these with the operator before the first run; they are the Release
workflow's inputs:

- `package`: the skill's argument.
- `increment`: PATCH, MINOR, MAJOR, PRE (next pre-release) or FINAL (promote
  a pre-release). Ask; do not guess.
- `prerelease`: none, a, b or rc. Default none.
- `version`: only to type the exact version, X.Y.Z or a pre-release
  X.Y.Z{a,b,rc}N (for example 0.2.0rc1), with no v. A package's
  first release needs it; kmaudit had none before its first.

## 1. Dry run

```sh
gh workflow run release.yml -f package=<package> -f increment=<increment> -f prerelease=<prerelease> -f dry_run=true
gh run list --workflow release.yml --limit 1
gh run watch <run-id> --exit-status
gh run view <run-id> --web
```

Add `-f version=<version>` when the operator typed one. The run's step
summary shows the tag and the notes a real run would commit, and says whether
they are Hermes' rewrite or the draft. When the run fails, quote the failing
step's `::error::` and stop.

## 2. Real run

Once the dry run passes and the operator agrees, run it from main:

```sh
gh workflow run release.yml --ref main -f package=<package> -f increment=<increment> -f prerelease=<prerelease> -f dry_run=false
gh run list --workflow release.yml --limit 1
gh run watch <run-id> --exit-status
```

It opens the version pull request from the branch `release/<tag>`.

## 3. Review the notes in the version pull request

```sh
gh pr list --head release/<tag>
gh pr view <number>
gh pr diff <number>
```

Read `.github/release-notes/<tag>.md` in the diff and the pull request body.
When Hermes' rewrite was kept, the body ends with the draft's What changed
section: check each rewritten line against it. Also check that every change
the release holds has a line.

When the notes miss a change or read badly, edit the file on the release
branch and push. The file is what release-tag publishes; the body is not
updated.

```sh
git fetch origin release/<tag>
git switch release/<tag>
# edit .github/release-notes/<tag>.md
git commit -am "release: edit the <tag> notes"
git push
```

When the draft left out a change it should have listed, also fix
`scripts/release_notes.py`, with a test, in its own pull request.

The workflow bot opens the pull request, so no checks run on it until it is
closed and reopened (`gh pr close <number>` then `gh pr reopen <number>`).
Never merge it with `--admin`. Merging is the operator's approval: merge only
when they say so.

## 4. After the merge, watch release-tag

```sh
gh run list --workflow release-tag.yml --commit <merge-sha>
gh run watch <run-id> --exit-status
gh run view <run-id>
gh release view <tag>
```

release-tag runs one job per package; the other package's job says there is
nothing to release. When commits reached main between the draft and the
merge, the job still publishes the reviewed notes unchanged, but writes a
`::warning::` naming those late commits, and a step summary section "Commits
missing from the <tag> notes" (`gh run view <run-id> --web`). `gh run view`
lists the warning among the run's annotations. `gh release view <tag>` cannot
show them: they are the commits the notes leave out. Then read the published
notes with `gh release view <tag>` for any other change they miss.

## 5. Close a gap without losing the reviewed text

The published notes are the reviewed file: Hermes' rewrite plus any edits
made in the pull request. When a late commit or any other change the release
holds is missing:

1. Add the missing entry by hand to the published notes, keeping the rest of
   the text, and set them:

   ```sh
   gh release view <tag> --json body --jq .body > notes.md
   # add the missing entry to notes.md
   gh release edit <tag> --notes-file notes.md
   ```

2. Make the same edit to `.github/release-notes/<tag>.md` in a follow-up pull
   request, so the repository and the Release say the same thing.
3. When the draft missed a change it should have listed (not a late commit),
   also fix `scripts/release_notes.py`, with a test.

Never regenerate published notes from the script. That would replace the
reviewed prose with the raw draft and leave the committed file saying
something else.
