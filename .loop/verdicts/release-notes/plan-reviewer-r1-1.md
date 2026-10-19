---
type: verdict
title: 'Verdict: release-notes plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-notes: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T12:51:35+00:00'
slug: release-notes
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan holds. Its one listed risk, that first-parent history might not give each release useful entries, is settled by spike release-notes/1. I found no unlisted risk that would break the approach, the scope or the contract.

## Checked

- Spike release-notes/1: README outcome, stdout.txt (per-range counts and every surviving plain subject), an empty stderr.txt, and run.json (exit 0, not truncated). The evidence answers the risk. Every range from v0.2.0..v0.3.0 on has 1 to 20 loop merges, and the only noise left was the operator: and chore; manual subjects, which the plan and row r2 now skip.
- `.github/workflows/release-tag.yml`: checkout uses fetch-depth 0, so tags and full history are there in CI. The annotated tag is created locally before the publish step, so a script that refuses unknown tags still finds the new one. The workflow already finds the previous tag, so moving from --generate-notes to --notes-file is a local change to one step.
- History: v0.10.0 and v0.9.1 tag the release pull request merges on main's first-parent line. The first-parent walk of v0.9.1..v0.10.0 holds `Merge loop/drop-summary-nudge` and the uv cache commit, as row r5 expects. Across all of main's first-parent history, the only merges other than loop merges and release pull requests are three `Merge remote-tracking branch 'origin/main'`, which the plan skips.
- `tests/scripts/test_workflows.py` exists and already asserts on release-tag.yml, including `--notes-start-tag`. The plan's workflow test is an extension of it. ADR 0012 exists at the path named.
- Gates: `uv run pytest` covers tests/scripts. `.github/release-notes.md` is outside the kmctl-check and okf-validate hook paths, so the template is not held to OKF front matter.

## Findings

None.

## Notes

The existing test `test_release_tag_builds_before_it_tags_and_publishes_the_release` asserts that `--notes-start-tag` is in the run text. With --notes-file that flag goes away, so the test has to change with the workflow. This is a build detail, not a risk to the plan. The plan also needs the script to take a repository path, or to run from the cwd, so the scratch-repo tests can point at it. That is also a build detail.
