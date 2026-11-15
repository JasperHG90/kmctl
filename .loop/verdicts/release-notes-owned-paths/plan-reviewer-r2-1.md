---
type: verdict
title: 'Verdict: release-notes-owned-paths plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of release-notes-owned-paths: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:34:46+00:00'
slug: release-notes-owned-paths
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved. release-tag will call `scripts/release_paths.py`, not `release_notes.py`, so `test_release_tag_never_writes_its_own_notes` (which asserts the string `release_notes.py` is absent from release-tag.yml) and ADR 0012's "it no longer runs `release_notes.py`" still hold. Nothing else I found could break the plan.

## Checked

- The listed risk is still settled by spike:release-notes-owned-paths/1 (7 of 43 kept commits dropped, none shipped). The round 1 check that none of the four paths ships in kmctl's wheel or sdist still applies.
- The awk in release-tag's late-commit step and `owns` in scripts/release_notes.py are the only two copies of the rule. No doc, skill or test outside `.loop/` restates "every path outside packages/" apart from ADR 0012 lines 168-170, and the plan's `touches` already lists that ADR.
- Importing the shared script works as planned. `uv run scripts/release_notes.py` puts `scripts/` first on sys.path, so `from release_paths import owns` resolves. No test imports `scripts.release_notes` as a module, because test_release_notes.py runs it as a subprocess.
- 2.0 facts: one problem, one goal and one behaviour outcome. They match the prose, and `touches` covers the new script, both callers, both test files and the ADR.

## Findings

- p1 (resolved): release-tag now calls scripts/release_paths.py, so it never names release_notes.py and the guard and ADR 0012 line stand unchanged.

## Notes

These are for the build, not findings.


- The late-commit tests run the step in a temporary repo, so a relative `scripts/release_paths.py` will not exist there. Give the step the real path (env var, or copy the script into the temp repo).
- Other tests here import scripts as `scripts.X`. If release_notes.py does `from release_paths import owns`, it works as a script but would fail if imported as `scripts.release_notes`. Keep release_paths.py free of third-party dependencies, so release-tag can run it once per late commit without resolving packages.
