---
type: verdict
title: 'Verdict: kmctl-to-packages plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of kmctl-to-packages: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T19:55:54+00:00'
slug: kmctl-to-packages
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

Fail, but both findings are revisions, not a rethink. p5 is resolved: action.yml, the starter justfile and its test now ship with O1. p6 stays open in a new form: tagging the test copy one minor past its own version makes the tag, the copy's copier default and the installed CLI's version disagree, so the starter bootstrap either asks for a missing tag or fails doctor's lock check. p7 is new: the pin integration test pins v0.5.1, not tree_repo's tag, so it needs O2 and a post-cutoff ref, and O1 cannot claim it.

## Checked

- Re-read the whole plan and eval rows; prior verdicts r1 and r2.
- tests/conftest.py tree_repo (tags `v{version('kmctl')}`), the autouse KMCTL_PINNED=1 fixture (so the starter bootstrap does not hand off), tests/test_starter.py _bootstrap and test_bootstrap_installs_this_checkout (copier defaults, `kmctl doctor --json` must be ok), copier.yml kmctl_ref default, starter/justfile.jinja and apm.yml.jinja using kmctl_ref.
- src/kmctl/doctor.py:373 lock check against package_ref(); src/kmctl/plugin.py package_ref = v + cli_version.
- tests/test_pin.py integration test: lock at OTHER = v0.5.1 with tree commit, KMCTL_PINNED unset, real uvx.
- scripts/release.py set rewrites the four apm.yml files, copier.yml's default and the pinned lines, so it can bump a copy coherently.
- Risks 1, 3, 4 stay settled by spikes 1/3, 2/4 and 5; risk 2 by operator acceptance.

## Findings

- p1, p2, p3, p4, p5: resolved.
- p6: the test-only tag must come with a matching version in the copy (release.py set on the copy), or the starter bootstrap fails on a missing tag or on doctor's lock check.
- p7: the pin integration test pins v0.5.1 and really hands off; it needs O2's fragment and a ref above v0.12.1, so it belongs in O2's checked-by, not O1's.

## Notes

- No split needed. With p6 and p7 fixed, O1 ships alone on the starter and knowledge-job checks, and O2 owns the real-uvx pin test.
