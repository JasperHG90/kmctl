---
type: verdict
title: 'Verdict: root-release-cutoff plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of root-release-cutoff: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T04:48:59+00:00'
slug: root-release-cutoff
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved: the plan moves LAST_ROOT_RELEASE into plugin.py, gives HOOK_INSTALL and the pin hand-off one helper that decides the fragment for a version, adds test_plugin.py to touches and a hook-hint test to checked-by. I found no other risk that could break the plan.

## Checked

- The import direction holds. pin.py:28 imports from kmctl.plugin, and plugin.py imports nothing from pin.py, so the constant has to live in plugin.py, as the plan says.
- Tags in the clone: v0.8.0 through v0.12.2 have no packages/kmctl/pyproject.toml, and no tag after v0.12.2 exists yet. The remote has the same v0.12.x tags. The tag integration test passes with the cutoff at v0.12.2, and no rc tag of 0.12.2 sits in the way.
- In the starter, the jinja strips the a/b/rc suffix before it compares, so v0.12.3rc1 becomes [0,12,3] and gets the fragment, and v0.12.2 becomes [0,12,2] and gets none. That matches the parametrised cases in checked-by.
- release.py adds SUBDIRECTORY to install lines and to the hooks.json hints (lines 77-87 and 292). Making it follow the cutoff keeps hooks.json equal to HOOK_COMMAND at 0.12.2 (test_plugin.py:57 and :110), because both sides drop the fragment together. The test that the two cutoffs agree guards this.
- kmaudit's install line has its own tags (kmaudit-v) and its own regex, so the kmctl cutoff does not touch it.
- The installed kmctl is 0.12.1 on this branch, and `set 0.12.2` moves it to main's v0.12.2 lines with no fragment.

## Findings

- p1: resolved. The plan now covers the fifth cutoff site in HOOK_INSTALL and tests it.

## Notes

- The new helper in plugin.py needs a version parser. Today `_version` is in pin.py, so it either moves or gets copied, and the plugin helper should treat a version it cannot parse (a dev build) the way uvx_source treats a non-tag ref. That is a build detail, not a plan risk.
- The 2.0 facts match the prose. One problem and one behaviour outcome; touches now include plugin.py and test_plugin.py.
