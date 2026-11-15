---
type: verdict
title: 'Verdict: release-notes-owned-paths plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-notes-owned-paths: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:22:33+00:00'
slug: release-notes-owned-paths
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works. The spike shows that taking `.loop/`, `.okf/`, `.claude/` and `uv.lock` away from kmctl drops 7 of 43 kept commits and nothing else, and none of the 7 ships. I confirmed that none of the four paths goes into kmctl's wheel or sdist. One gap needs a revision: the plan moves release-tag onto `release_notes.py` without saying how the existing "release-tag never runs release_notes.py" guard and ADR line change. That guard protects the rule that published notes are never regenerated.

## Checked

- The plan's only listed risk is settled by spike:release-notes-owned-paths/1. I read the README outcome, stdout.txt and run.json (exit 0, per-range counts, the 7 dropped commits named). The evidence answers the risk.
- What actually ships: packages/kmctl/pyproject.toml builds the wheel from `src/kmctl` plus apm `.apm/skills`, `.apm/agents` and `claude/.apm/instructions`, and the sdist force-includes the same. Nothing comes from `.okf/`, `.claude/`, `.loop/` or `uv.lock`, so the premise holds. The wheel's dependencies come from the package pyproject, not the lock.
- `owns` in scripts/release_notes.py and the awk in release-tag.yml's "Name commits that landed after the notes were drafted" step encode the same rule today, as the plan says. Nothing else in scripts/ or .github/ copies it.
- release-tag sets up uv before the step, so `uv run scripts/release_notes.py --owns` can run there.
- The release-per-package-reviewer-f1 plan edits the Drafted-From lookup (its awk at the top of the same step), not the ownership awk. The two plans change different lines of one step, so expect a merge conflict but no clash in meaning.
- 2.0 facts: one problem, one goal and one behaviour outcome. They match the prose, and `touches` covers every file the prose changes.

## Findings

- p1: release-tag.yml would call release_notes.py, which collides with test_release_tag_never_writes_its_own_notes and ADR 0012's statement that release-tag no longer runs it. The plan must name the narrower guard that keeps "published notes are never regenerated" enforced.

## Notes

These are for the build, not findings. The late-commit tests run the step with bash in a temporary repo as the working directory, so a relative `scripts/release_notes.py` will not exist there. The test needs to give the step the real script path, through an env var or by copying it in. Each `uv run` of an inline-metadata script also resolves `packaging`, which may need the network or the uv cache in the test environment.
