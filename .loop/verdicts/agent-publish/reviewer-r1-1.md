---
type: verdict
title: 'Verdict: agent-publish reviewer round 1'
description: 'reviewer verdict for round 1 of agent-publish: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T07:56:04+00:00'
slug: agent-publish
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change can land after one small wording fix. `publish` does what the plan
says: it creates the issue, or edits it and adds a comment with the mentions;
below the threshold it closes an open issue with a comment; owners come from
the last `*` rule of the first CODEOWNERS file; it exits 1 when gh fails and
2 for a bad report. The token and the agent are kept apart as the three plan
rounds required: the audit job has `contents: read`, no token and no cache.
The publish job is a fresh runner with `issues: write`, a checkout with
`persist-credentials: false`, setup-uv with the cache off, and the artifact
downloaded into `$RUNNER_TEMP`. One finding, not blocking: the agent's
refusal message, and the how-to's quote of it, still tell users to give the
token to "the step that posts the report".

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests and integration
  pass, rows r1 to r7 pass, "stamp green: 25f04f65ae90ac4c8e03fdaa021222322fa03168eab2dcd8c125f6563446148a".
- Read the whole diff in action/agent.py, action.yml, the workflow, both test
  files, scripts/release.py and its tests, ADRs 0012 and 0017, the overview,
  the log and the how-to.
- r1: `test_publish_below_threshold_posts_nothing` asserts no create, edit,
  comment or close. `..._closes_open_issue` asserts a comment on #7 that
  names the threshold, then a close, in that order, and no create or edit.
- r2: create with the default title, both findings in the body and the run
  link. Edit on #7 rather than a create, plus a comment with `@alice` and
  "2 high". The stub lists "Knowledge audit 2", which also checks exact
  title matching.
- r3: last `*` rule wins and comments are stripped. .github/ beats the root
  file, which beats docs/. `--mention` replaces the owners and gets an `@`
  added when missing. With no owners there is no cc line.
- r4: a failing gh exits 1 and creates nothing. A missing file, bad JSON or
  a report without findings exits 2 with a message and no gh call.
- r5: tests check workflow-level permissions are exactly `contents: read`,
  that the audit job sets none and holds no token. The publish job has
  `needs: audit` and `{contents: read, issues: write}`. Every setup-uv sets
  `enable-cache: false` and no actions/cache is used. In the action, only
  the publish step holds the token, and the new inputs are wired through env
  (no `${{ }}` in the shell text).
- r6: `kmctl check` is clean and nothing names knowledge-audit-issue.sh.
- r8 (judgment): `uv run --script action/agent.py publish --help` lists
  report, --min-severity (choices and Default: high), --title (Default:
  Knowledge audit), --mention (Repeatable, default the CODEOWNERS owners)
  and --repo (Default: the current folder), with exit codes in the
  description. That meets the row.
- release.py: the new `- uses: JasperHG90/Knowledge-management@v0.3.0` line
  in the how-to matches `_USES`, so DOC_LINES 6 is right. ADR 0012 has a
  correction recording it.

## Findings

- f1 (open, docs, non-blocking): action/agent.py:481 and
  docs/how-to/install-the-plugin-and-the-ci-action.md:342 should say to
  give the token only to the publish job (a separate job), not to "the step
  that posts the report". Update both together.

## Notes

- A report larger than GitHub's 65536-character body limit makes gh fail,
  and publish exits 1. The old shell script behaved the same way, so this
  is no regression.
- In action.yml's publish mode, CODEOWNERS is read from `inputs.path`. With
  a subfolder `path`, a root CODEOWNERS is not found. The default "." is fine.
