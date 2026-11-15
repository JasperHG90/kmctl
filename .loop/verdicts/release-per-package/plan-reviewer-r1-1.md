---
type: verdict
title: 'Verdict: release-per-package plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-per-package: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T17:51:31+00:00'
slug: release-per-package
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: one Release run with a package input, a per-package version source and tag family, path-filtered notes committed in the version pull request, and a release-tag matrix that publishes the committed file or refuses. The one listed risk (can kmctl's moved pyproject still read apm/apm.yml?) is settled by spike kmctl-to-packages/3. Three things must be fixed before building. The late-commit warning is in the prose and in r5 but in no outcome (p1). Its marker lives in a file the Hermes ticket rewrites and strips comments from (p2). And the merge that adds kmaudit's VERSION file fires release-tag into a failed kmaudit-v0.1.0 release (p3). None of these needs a rethink.

## Checked

- Read the plan, its eval rows, the epic brief, release-notes-hermes's plan and kmctl-to-packages's plan.
- Spike kmctl-to-packages/3 (as cited in kmctl-to-packages's own risk list): all four builds report apm.yml's version with the hook. That settles the listed risk. Spike release-flow/1 backs the regex-source claim for kmaudit's VERSION file.
- Code: scripts/release_notes.py (it refuses an unpushed tag and has a v*-only previous_tag and a release/v skip pattern, which matches P3), release-tag.yml (it watches only apm/apm.yml, runs a bare uv build, generates notes at publish time and passes no --latest, which matches P5), release.yml (no package input, a fixed body, which matches P4), and release.py (compare with an empty OLD gives raised, which is the basis of p3).
- uv.lock: kmaudit's entry has `version = "0.1.0"` and kmctl's dynamic entry has none, which matches the P2 claim. packages/kmaudit/README.md has the install line O2 pins. tests/scripts/test_release_docs.py exists.
- Problems, goals and outcomes: P1 to P5 each map to one outcome and the needs chains are right. O4 and O5 are the behaviours that can ship and O1 to O3 are support. The gap is p1.
- Eval rows r1 to r4 match O1 to O4. r5 asks for more than O5 lists (p1).

## Findings

- p1: the late-commit marker and warning are in the prose and r5 but in no outcome, so plan.split cannot assign them.
- p2: the marker sits in the file release-notes-hermes replaces, and that plan strips HTML comments, so the seam loses it. The release branch's parent commit already records the drafted commit.
- p3: adding packages/kmaudit/VERSION trips release-tag (empty OLD counts as raised) into a refused kmaudit-v0.1.0 release on main, and leaves 0.1.0 unreleasable.

## Notes

- kmaudit has no kmaudit-v* tag yet, so its first draft walks the whole history: every commit that ever touched packages/kmaudit, not the 3 bullets measured since v0.12.1. That is not a break, because the notes are reviewed in the pull request, but the prose's figure describes a later release.
- In a dry run the bump job does not run, so the draft step has to sit in a job that runs in dry runs, and the file has to reach bump (as an artifact or by drafting again). The build can settle that, but the Hermes ticket's step must sit in the same place.
