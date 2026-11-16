---
type: verdict
title: 'Verdict: adr-kmaudit-stale-lines plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of adr-kmaudit-stale-lines: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T06:59:27+00:00'
slug: adr-kmaudit-stale-lines
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p2 is resolved. The plan now corrects ADRs 0001, 0011, 0012, 0014 and 0020 and the index notes for 0012 and 0014, and row r1 covers all five ADRs. Nothing else I found could break it.

## Checked

- Grepped `.okf/decisions/` again for `apm/` and `packages/kmaudit/VERSION` outside the new paths. The remaining hits are the ones the plan names and leaves alone: 0013, 0016 and 0028 are deprecated; 0024 and 0031 mention `apm/` only as a rejected option or in Context; 0044 already carries its own ADR 0045 amendment. 0030's hit is an external microsoft/apm URL, and the hits in 0037, 0040 and 0043 are `packages/*/apm` paths, so none of them is stale.
- Index notes for ADRs 0011 and 0020 name no `apm/` path, so only the 0012 and 0014 notes need edits, which matches the plan.
- `release-tag.yml`'s paths filter is exactly `packages/kmctl/apm/apm.yml` and `packages/kmaudit/apm/apm.yml`, so the plan's claim about what release-tag watches holds. Both folders exist, and there is no root `apm/`.
- Problems, Goals and Outcomes match the prose: one problem (stale package paths and version sources in five ADRs and the index), one goal, and one behaviour outcome that ships alone with `needs: none`. Touches list all five ADRs, the index and the test file, and checked-by lines up with rows r1 and r2.

## Findings

- p1 (resolved): the index and test file are in scope and in touches.
- p2 (resolved): ADRs 0011 and 0020 get dated ADR 0045 corrections, are in touches, and row r1 checks them.

## Notes

- As in round 2, the index note for ADR 0014 will stop matching that ADR's front matter `description`. No check enforces the match, so this does not block.
