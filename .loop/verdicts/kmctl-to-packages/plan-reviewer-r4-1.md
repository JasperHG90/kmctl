---
type: verdict
title: 'Verdict: kmctl-to-packages plan-reviewer round 4'
description: 'plan-reviewer verdict for round 4 of kmctl-to-packages: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T20:06:11+00:00'
slug: kmctl-to-packages
pass: plan-reviewer
round: 4
body_schema: verdict/1
---

## Summary

Pass. p6 and p7 are resolved as described. Nothing left would stop O1 shipping alone or make a checked-by impossible; two build details follow for the builder.

## Checked

- Whole plan against round 3; tree_repo, served, apm_install in tests/conftest.py; scripts/release.py set_version and main (needs only the files, not git); tests/test_pin.py real-uvx test; integration tests using served (doctor, plugin_patch, apm_package, opencode, antigravity).
- Risks 1, 3, 4 stay settled by spikes 1/3, 2/4, 5; risk 2 by operator acceptance.

## Findings

- p1, p2, p3, p4, p5: resolved in earlier rounds.
- p6: resolved; tree_repo bumps the copy with release.py set before tagging.
- p7: resolved; the real-uvx claim sits in O2 and pins the test-only tag.

## Notes

For the builder, not blocking:

- `served` also calls tree_repo, and its consumers ask APM for `v{version('kmctl')}` (conftest apm_install) or `plugin.package_ref()` (test_plugin_patch.py:427), then run the in-process CLI at 0.12.1, and test_doctor_after_a_real_install_exits_zero needs doctor's lock check to pass. If tree_repo always bumps, those refs miss the tag; if they ask for the bumped tag, doctor's lock check sees a pin the CLI does not report. Make the bump opt-in (a tree_repo parameter used by the starter bootstrap and the real-uvx pin test) and leave served at the current version. That still meets O1's checked-by.
- test_hands_off_through_a_real_uvx asserts the handed-off copy reports `version('kmctl')`; with the bumped copy it reports the test-only version (the PATH half stays 0.12.1), so the expected strings change.
