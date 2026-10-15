---
type: verdict
title: 'Verdict: new-concept-verbs plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of new-concept-verbs: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:12:50+00:00'
slug: new-concept-verbs
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The approach works and the validator premise holds. Three gaps in scope and contract need fixing before building. The plan has no step for creating a section on its first page, which scaffold-init hands to this ticket. It assumes a root index count with no defined format. And it leaves the command's inputs and existing-file behaviour open, which a downstream ticket depends on. None of them makes the plan unworkable, so this is fail, not reject.

## Checked

- The plan lists no risks ('none'). There are no spikes and no eval rows yet.
- The validator premise: okf_validate.py 0.10.1 exists locally at ~/.claude/plugins/cache/scaccogatto/okf/0.10.1/skills/validate/scripts/okf_validate.py, with LICENSE and NOTICE beside it. It runs with pyyaml under `--strict` and passes the current .okf/ cleanly. It accepts any non-empty `type`, a bare-date `stale_after`, nested prototype folders with README.md, and an index with no front matter. It does not check index links or counts, so 'passes the validator' will not catch p1 or p2.
- scaffold-init's plan defers section creation to the verbs. decision-supersede's plan depends on this ticket. handoff-and-continue-skills' plan expects `kmctl new handoff` to save and update a handoff.
- .claude/rules/okf-bundle.md: decisions are numbered NNNN, sections are created with their first page, and the root index carries one link per section plus a count.
- src/kmctl/__init__.py: only a Typer root with --version so far. pyproject has no pyyaml dev dependency yet. The plan says the first ticket that needs the validator adds it, which is fine.

## Findings

- p1: first-page section creation and the root index link are missing from scope.
- p2: the root index count is free prose with no format kmctl can rely on.
- p3: the description and body inputs and the existing-file behaviour are not defined, and handoff-and-continue-skills depends on them.

## Notes

The okf-bundle rule also wants each new concept named in log.md. Whether kmctl appends that line or the agent does is worth one sentence in the revised plan, but building will answer it. One ticket with five kinds is still one piece of work. These findings do not call for a split.
