# Releases come from CI and carry notes

A release goes through CI (ADR 0012). Run the Release workflow
(`release.yml`) as a dry run, then for real, which opens the version pull
request. Merging that pull request is the approval: `release-tag.yml` tags
the merge commit and publishes the GitHub Release, with notes from
`scripts/release_notes.py`. The workflow bot opens the version pull request,
so no checks run on it until it is closed and reopened; never merge it
past branch protection with `--admin`.

<constraint name="every-release-has-notes">
WHY: a release whose notes say "None." tells users nothing changed, and
nobody reads the commit log to find out otherwise. v0.12.0 shipped six
pull requests that way.

After a release publishes, read its notes with `gh release view TAG`. If
they leave out a change the release holds, fix `scripts/release_notes.py`
rather than writing the notes by hand, then regenerate the notes and set
them with `gh release edit TAG --notes-file FILE`. Do the same for every
earlier release whose notes the fix changes.
</constraint>
