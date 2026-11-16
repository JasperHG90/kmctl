---
type: verdict
title: 'Verdict: decision-candidates plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of decision-candidates: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T16:04:38+00:00'
slug: decision-candidates
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan can work as written. It lists no risks, and I found none that would break it. The split it copies from the prototype runs harmlessly on repositories without the loop harness. The verb writes nothing, so it should not print a `Next:` line. Leaving the decision index out of the output is sound. 0047 is the next free number and fits as a new ADR. Problems, Goals and Outcomes match the prose.

## Checked

- Read the plan, its eval rows r1 to r3, ADR 0046, and the prototype's README, `units.py`, `signals.py` and `hide.py`.
- Read `scripts/release_notes.py` (`_first_parent`, `_SKIP`, `_TICKET`, `_PULL`, `_SYNC`), which `units.py` imports.
- Read the `decision` group, `next_step` and its `--json` call sites in `packages/kmctl/src/kmctl/__init__.py`, plus `.claude/rules/cli-interface.md`, `packages/kmctl/tests/test_help.py` and the `decision` rows of `docs/reference/commands.md`.
- Checked that 0046 is the highest record and that no other plan claims 0047.
- Read the follow-on plan `decision-gaps-skill` to see what it expects from this verb.

## Findings

None.

## Notes

- Skip list. The walk and skip patterns live in `scripts/release_notes.py`, a repo script that the installed package cannot import. So `candidates.py` must carry its own copy, and the walk then exists twice in this repo. Expect that drift risk, or have `release_notes.py` import from kmctl later. On other repositories the loop-specific patterns (`loop: `, `Merge loop/SLUG:`, `operator: manual commits`, the `release/v` PR branch) simply never match. Those repos fall back to one change per PR merge or first-parent commit, which is the useful general case. Their own release commits (`chore(release): ...`) are not skipped, so they get listed and judged, at about two cents each. That costs little and drops nothing. Keep the list. Put it in one named constant and say in the help epilog and the reference what gets left out, so a user on another repository knows.
- Next line. The rule asks for `Next:` only on verbs that write files, and this one writes nothing, so leaving it out fits. The follow-on `decision-gaps-skill` plan wants this verb's output to end with a `Next:` line that names the skill. That conflicts with `next_step`'s contract that the last step is a kmctl verb. Settle it in that ticket. Either way, print the line only in table mode, never under `--json`, the way existing verbs return early on `--json`.
- Decision index. Leave it to the judge. Under the default `--since`, the range starts after the newest record, so the index at HEAD is close to the index at each change's parent. The only differences are amendments, and the `recorded` field already shows those. With an older explicit `--since`, the skill can read `git show PARENT:.okf/decisions/index.md`. Every change already carries its first parent, so it needs nothing more from this verb.
- Plan path. The prototype's `hide.intent` also looks in `.loop/archive/SLUG/plans/README.md`. The plan names only `.loop/plans/`, so archived tickets would get no plan path. This is a small gap to settle while building.
- Group help. The `decision` group help and its reference row say "Change decision records ... Needs a bundle from kmctl init". A read-only verb that also runs with no records makes both wrong. Both files are already in `touches`, so rewrite those lines when adding the verb.
- ADR 0047. It fits as a new record. ADR 0046 only placed the scan in kmctl and left building it to the measurement. 0047 records the list/judge/report split and three rejected options. Note that the prototype README still calls the verb `kmctl decision gaps`.
- Facts. P1, G1 and O1 match the prose. O1 is a behaviour that can ship alone, and its touches cover every file the prose names. `seen by: calling code` is a fair reading for an agent that consumes `--json`.
