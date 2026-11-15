---
type: verdict
title: 'Verdict: upgrade-from-v0-12-docs plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of upgrade-from-v0-12-docs: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T19:46:53+00:00'
slug: upgrade-from-v0-12-docs
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved. The plan now writes the full entry (`path: packages/kmctl/apm`, `ref: vX.Y.Z`) into the docs, keeps `kmctl doctor` only as the final check after `apm install`, and the O1 checked-by line tests exactly that.

## Checked

- The order still holds: install the CLI first, then edit the entry, then `apm install` and `kmctl plugin patch`, then doctor. Once `apm install` updates the lock, doctor runs the new release, so the final check works.
- The files in `touches` exist: `packages/kmctl/README.md` (it has an Upgrade section), `docs/how-to/install-kmctl-with-apm.md`, `packages/kmctl/tests/test_docs.py`. The link target `packages/kmaudit/README.md` exists too.
- The 2.0 facts still match the prose: one problem, one goal, one behaviour outcome with no needs.

## Findings

- p1 (resolved, premise): the docs now carry the full entry, and doctor is only the final check. No new risk found.
