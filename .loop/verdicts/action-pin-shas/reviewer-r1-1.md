---
type: verdict
title: 'Verdict: action-pin-shas reviewer round 1'
description: 'reviewer verdict for round 1 of action-pin-shas: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:05:10+00:00'
slug: action-pin-shas
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change pins all three `uses:` lines in `action.yml` and all six in `knowledge-audit.yml` to the commit SHAs the plan names, each with its version as a comment. It also adds both files to `test_every_action_is_pinned_by_commit_sha`. Each SHA matches its upstream tag, and each action now runs at a single version across the repo. Nothing blocks.

## Checked

- Diff against HEAD: `action.yml`, `.github/workflows/knowledge-audit.yml` and `tests/scripts/test_workflows.py`, nothing else.
- r3 (judgment): I resolved each tag with `gh api repos/OWNER/REPO/commits/TAG`. checkout v7.0.1 = 3d3c42e5…, setup-uv v10.2.0 = c18668ad…, upload-artifact v7.0.2 = cf430e03…, download-artifact v8.0.2 = 90008…8333. All four match. v8.0.2 and v7.0.2 are each repo's latest release. Grepping every `uses:` under `action.yml` and `.github/workflows/` shows one SHA per action.
- Upgrade risk: I read the release notes for the major versions skipped. setup-uv v7 to v10 changes cache defaults, the manifest format and `server-url`. Both files set only `enable-cache: false`, so none of that affects them. upload-artifact v7 and download-artifact v8 keep the `name`/`path` inputs. v8's digest-mismatch check now fails the run by default, which is the safer behaviour. checkout keeps `fetch-depth` and `persist-credentials`.
- r1/r2: the test regex requires `owner/repo@<40 hex> # vX.Y.Z` at the end of each `uses:` line, and `assert lines` guards against an empty match. I checked by hand that a tag ref and a SHA with no comment both fail the regex. r1's `-k ... and action` selects all four parametrized cases, including `action.yml`, as the builder said. r2 selects `knowledge-audit.yml`.
- Docs: the `@v4` examples in `docs/how-to/install-the-plugin-and-the-ci-action.md` are readable tags on purpose, and the plan puts them out of scope. No doc or docstring now says something false.
- `loopctl gate stamp`: lint, format, tests, integration, r1 and r2 all pass. "stamp green: 0c25e498e46db5b25e8eb3b12917328c4225f06d1f4599938193d429b9e92017".

## Findings

None.

## Notes

The new pins run on Node 24, which needs Actions runner 2.327.1 or later. That only matters for consumers on old self-hosted runners. GitHub-hosted runners already qualify.
