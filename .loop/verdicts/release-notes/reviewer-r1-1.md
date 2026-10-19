---
type: verdict
title: 'Verdict: release-notes reviewer round 1'
description: 'reviewer verdict for round 1 of release-notes: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T13:02:28+00:00'
slug: release-notes
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. `scripts/release_notes.py` walks main's first-parent history between the previous release tag and the given one, sorts ticket merges and plain commits into two sections, skips the noise the plan lists, and fills `.github/release-notes.md`. `release-tag.yml` now writes the notes with the script and publishes them with `--notes-file`. The tests check each eval row's failure condition, and ADR 0012 matches the code. I found nothing to fix.

## Checked

- Gates: `loopctl gate stamp` from the worktree gave all green: lint, format, tests, integration and eval rows r1 to r6 pass, stamp 6ef025dcf2bd0a6435bd9e237af4c8be94f2b4a4542925a80e5e0ad8adbfbefd. `prek run --files` on the changed files passed too (kmctl check, ruff, okf validate --strict).
- Code read in full: the script, the template, the new test file, the workflow and test_workflows diffs, the ADR 0012 addition and the summary.md re-ack. The summary's `checked.against` list shrinking to 0012 alone is what `kmctl summary ack` writes (the concepts changed since the last check), not lost data.
- Workflow: checkout uses fetch-depth 0, so tags are there. On a raised run the tag is created locally before the publish step, and on a resume run it is fetched, so the script's unknown-tag refusal never fires wrongly. Under `set -euo pipefail` a failed script fails the step before `gh release create` runs. The previous-tag rule (packaging Version, pre-releases included) matches the old `sort -V` pipeline it replaces.
- Real history: I ran the script for all 12 tags. Every range has entries under What changed (v0.2.0 has 41; most have 1 to 8). Other changes hold no `loop:`, `release:`, release PR or branch-sync lines. v0.10.0 shows drop-summary-nudge and the uv cache commit (r5). The template's install lines match the forms the README and docs use.
- r1: the sections test checks exact section contents and that commits before v0.1.0, after v0.2.0 and inside the merged branch are absent. r2: parametrized over every noise subject plus the release PR merge. r3: template headings, both install lines pinned to the tag, the compare link names v0.2.0 for v0.3.0rc1, no leftover `$`, first release with no compare link, unknown tag exits 1 naming it with empty stdout. r4: asserts no `--generate-notes`, the script redirect into the notes file and that `--notes-file` uses it, in order. r6: the ADR names the script.

## Findings

None.

## Notes

v0.2.0's Other changes lists `operator: initial commit`. The plan only skips the `operator: manual commit` placeholder, so this is within contract; the operator may want to see it when reviewing the backfill.
