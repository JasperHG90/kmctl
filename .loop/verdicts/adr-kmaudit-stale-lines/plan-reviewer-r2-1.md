---
type: verdict
title: 'Verdict: adr-kmaudit-stale-lines plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of adr-kmaudit-stale-lines: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T06:57:28+00:00'
slug: adr-kmaudit-stale-lines
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Round 1's gap is fixed: the plan now corrects ADRs 0001, 0012 and 0014 and both index notes, and touches lists the test file. The approach still works, and the eval's switch to "a correction" rather than "the last section" holds up against the other ticket's 2026-11-16 correction to ADR 0012. One scope gap is left. ADR 0020 gives `apm/` and its two sub-packages as kmctl's package layout, and ADR 0011's latest rule-path correction names `apm/claude/...` and `apm/antigravity/...`. Neither has a correction for ADR 0045. This is the same kind of stale claim as ADR 0014's "kmctl's package is apm/", which the plan does correct. So G1 and P1 promise more than O1 delivers.

## Checked

- Plan and eval rows r1 and r2. Round 1 verdict.
- Grepped every ADR in `.okf/decisions/` for `apm/` paths outside `packages/kmctl/apm`, and for `packages/kmaudit/VERSION`, then checked which ones have a later correction or amendment pointing at ADR 0045. Only 0044 and 0045 mention 0045. 0044 corrects its own line 41.
- ADR 0013 is superseded by 0014, so leaving it alone is fine. ADR 0024 (`apm/opencode/`, a rejected option) and ADR 0031 (Context) mention `apm/` only as history. ADR 0028 is deprecated.
- ADR 0020: status stable, three corrections (2026-10-17, 10-19, 10-19). None touches the `apm/` layout in its Decision (line 61 onward).
- ADR 0011: the 2026-10-19 correction at line 187 is the latest word on where the rules live, and it names `apm/claude/.apm/instructions/`.
- `packages/kmctl/apm` holds `apm.yml`, `claude/` and `antigravity/`. There is no root `apm/`.
- `kmctl check`'s index check (`packages/kmctl/src/kmctl/checks.py`) only compares an entry's link text with the title or `ADR NNNN`, not with the description. So editing the index notes alone will not be undone by `kmctl check --fix`.
- Problems, Goals and Outcomes: one problem, one goal, one behaviour outcome that can ship alone, `needs: none`, and touches match the prose. The mismatch is in reach (p2), not shape.

## Findings

- p1 (resolved): the index and the test file are now in scope and in touches.
- p2 (open): ADR 0020's Decision and ADR 0011's 2026-10-19 correction still give `apm/` (with `apm/claude/` and `apm/antigravity/`) as where kmctl's package lives, with no ADR 0045 correction. G1 says the decisions describe where each APM package lives today, and that will still be false after this plan ships. Either add dated corrections to 0020 and 0011 (and their index notes if they name `apm/`), with a row for them, or narrow P1 and G1 to version sources only. The second option is awkward, because ADR 0014's "package in apm/" is a package-path claim the plan already fixes. Adding the two ADRs is the smaller and more consistent change.

## Notes

- The index note for ADR 0014 copies the ADR's front matter `description`, which also says "the APM package in apm/". Row r2 requires the index note to lose "in apm/", so the note will no longer match the description. No check enforces that they match, and the repo leaves descriptions alone as the original record elsewhere too, so this does not block. The implementer should know it is a deliberate divergence, though.
- `.okf/log.md` entries name `apm/apm.yml`. That is a log, so leave it.
