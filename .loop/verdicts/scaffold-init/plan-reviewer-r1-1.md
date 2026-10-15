---
type: verdict
title: 'Verdict: scaffold-init plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of scaffold-init: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:08:11+00:00'
slug: scaffold-init
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Fail on one blocking risk (p1). The approach (write five files if missing,
print what was created, no-op on a second run) is simple and fits the
manifesto and the typer skeleton in src/kmctl/__init__.py. The done criterion,
though, depends on an external okf validator whose reach from the test gate
is undefined, and the easy fixes either contradict ADR 0003 or hollow out the
criterion.

## Checked

- The plan's risk list ("none"): no spikes or acceptances to check.
- src/kmctl/__init__.py and pyproject.toml: typer app exists; no okf or
  pyyaml dependency.
- .okf/manifesto.md, ADR 0003, .claude/rules/okf-bundle.md: init's file set
  and "sections created with their first page" match the plan.
- The okf plugin: okf_validate.py lives only in the plugin cache under
  ~/.claude; it is a PEP 723 script needing pyyaml.
- .loop/config.toml gates: tests run as `uv run pytest`.

## Findings

- p1 (premise, blocking): no defined way for kmctl's tests to run the okf
  validator; see the claim. Settle by a spike or by naming the source in the
  plan.

## Notes

For the builder, not findings: the okf plugin ships a scaffolder
(skills/okf/scripts/okf_init.py) whose output passes `okf_validate.py
--strict`; its index.md and log.md shapes are a useful reference. The
validator rejects root index.md front matter keys other than okf_version or
upkeep and needs a non-empty `type` on manifesto.md. The eval has no rows
yet; the three done conditions in the Intent map directly to rows.
