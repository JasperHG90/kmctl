---
type: verdict
title: 'Verdict: root-release-cutoff plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of root-release-cutoff: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T04:47:31+00:00'
slug: root-release-cutoff
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The premise and approach hold; one consumer of the cutoff (plugin.py's HOOK_INSTALL) is missing from the plan and must be added before building.

## Checked


- `git ls-tree v0.12.2` has `src/` and no `packages/`, so v0.12.2 is a root release. The premise holds.
- pin.py:35 `LAST_ROOT_RELEASE = "v0.12.1"`, uvx_source compares `tag <= last`; starter/justfile.jinja:7
  `> [0, 12, 1]`; release.py:77 writes SUBDIRECTORY on every install line and hook hint (set_version,
  `_HOOK_INSTALL.subn(... {SUBDIRECTORY})`). All as the plan says.
- Merge with main: main's v0.12.2 install lines have no fragment, so `set 0.12.2` with the cutoff yields
  identical lines. That is the point of the plan and it holds.
- The starter bootstrap integration test bumps the tree one minor past the current version
  (conftest.bumped_version), so at 0.12.2 it tests 0.13.0 with the fragment. It keeps working.
- The tag integration test runs only in the loop gate (`uv run pytest -m integration`), where a full clone
  has the tags. CI does not run integration tests, so a shallow checkout does not matter.

## Findings

- p1: plugin.py HOOK_INSTALL always writes the fragment; it must follow the cutoff, with test_plugin.py in touches and a checked-by test.

## Notes

- Single behaviour outcome, one problem, one goal: the 2.0 facts match the prose apart from p1. One real
  risk, no split needed.
