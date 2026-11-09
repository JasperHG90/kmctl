---
type: plan
title: 'Plan: release-notes'
description: Each GitHub Release carries notes built from main's history between its tag and the one before, from a template, instead of GitHub's pull-request list.
tags:
- plan
generated:
  by: process:loopctl/2.2.1.dev16+g27435b040.d20261017
  at: '2026-10-19T12:48:28+00:00'
slug: release-notes
epic: null
depends_on: []
priority: null
---

# release-notes

Relayed from: none

## Intent

The operator (2026-10-19, ask j-20261019T123101+0000-6de3b719): "I'm unhappy
about the release notes on my releases. I.e. there are none. Remedy this for
the releases that already exist, make a release template, and ensure that
future releases get a proper release description."

Why they are empty: `.github/workflows/release-tag.yml` publishes with
`gh release create --generate-notes`, which lists merged pull requests. Work
lands on main as loop merges, not pull requests, so the only entry is the
release pull request itself ("release: v0.10.0 by @github-actions").

The history already says what changed. Each finished ticket leaves a
first-parent merge `Merge loop/SLUG: SUMMARY`, and changes made outside the
loop are plain commits on main.

What changes:

- **`new:scripts/release_notes.py`** prints a release's notes for a tag and
  the tag before it (none for the first release). It walks main's
  first-parent history between them: each `Merge loop/SLUG: SUMMARY` becomes
  a bullet under Changes, each other commit a bullet under Other changes. It
  skips `loop:` state commits, `release:` commits, release pull request
  merges, `Merge remote-tracking branch`, merges of main into a branch, and
  the `operator: manual commit` and `chore; manual commits` placeholders. It
  fills the template and refuses an unknown tag.
- **`new:.github/release-notes.md`** is the template: the changes, the other
  changes, the install line for that tag and a compare link to the tag
  before.
- **`.github/workflows/release-tag.yml`** writes the notes with the script and
  publishes with `--notes-file` in place of `--generate-notes`.
- **Tests** in `new:tests/scripts/test_release_notes.py` build a scratch repo
  with each kind of commit and check what lands where; `tests/scripts/test_workflows.py`
  checks the workflow uses the notes file and no longer generates notes.
- **ADR 0012** in `.okf/decisions/0012-releases-come-from-ci.md` gets a line
  on where the notes come from.

After landing, not part of the commit: the 12 existing releases (v0.2.0 to
v0.10.0) get their notes replaced with `gh release edit TAG --notes-file`,
after the operator sees one set.

Outcome: `uv run scripts/release_notes.py v0.10.0` prints notes whose Changes
list holds drop-summary-nudge and whose Other changes hold the uv cache
commit, with no `loop:` or `release:` lines; and every existing GitHub
Release's body is no longer GitHub's pull-request list.

## Could invalidate this plan

- First-parent history might not give each release a useful entry: a ticket
  could have landed by fast-forward with no `Merge loop/` commit, or ranges
  could be all noise. Then the script needs another source (the ticket
  ledger). Settled by spike:release-notes/1: in all 12 ranges every
  `loop: land SLUG` has its `Merge loop/SLUG`, every range from v0.2.0 on has
  1 to 20 of them, and the only noise the filter missed was the `operator:`
  and `chore; manual` subjects, now skipped.
