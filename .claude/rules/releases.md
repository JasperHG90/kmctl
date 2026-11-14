# Releases come from CI and carry notes

A release goes through CI (ADR 0012). The release skill,
`.claude/skills/release/SKILL.md` (`/release kmctl` or `/release kmaudit`),
walks the steps and says why `release.yml` and `release-tag.yml` both exist.
This rule keeps the two constraints that hold even when nobody runs it.

<constraint name="no-admin-merge">
WHY: merging the version pull request approves the version and its notes,
and `--admin` skips the checks that approval relies on.

Never merge the version pull request past branch protection with `--admin`.
The workflow bot opens it, so no checks run on it until it is closed and
reopened.
</constraint>

<constraint name="every-release-has-notes">
WHY: a release whose notes say "None." tells users nothing changed, and
nobody reads the commit log to find out otherwise. v0.12.0 shipped six
pull requests that way.

Review the notes in the version pull request, where they are committed as
`.github/release-notes/<tag>.md`, and edit that file there when they miss a
change. After the merge, read release-tag's warning about commits that
landed after the notes were drafted, then the published notes with
`gh release view TAG`. Add any change they leave out by hand, keeping the
reviewed text: to the published Release with
`gh release edit TAG --notes-file FILE`, and to the committed
`.github/release-notes/<tag>.md` in a follow-up pull request. When the
draft missed a change it should have listed, also fix
`scripts/release_notes.py`. Published notes are never regenerated from the
script, which would throw away the reviewed text.
</constraint>
