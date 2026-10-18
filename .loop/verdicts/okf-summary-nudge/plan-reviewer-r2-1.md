---
type: verdict
title: 'Verdict: okf-summary-nudge plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of okf-summary-nudge: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T21:54:39+00:00'
slug: okf-summary-nudge
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The revision fixes p1 for copies on PATH from this release on. It misses copies already installed: v0.7.0 and v0.8.0 hand off before Typer parses, so they send the nudge through uvx online after every tool call in a project pinned to another release. The plan's claim that an older copy only prints a usage error is false for them. Setting KMCTL_PINNED=1 in the hook command fixes this without touching hand_off, so the plan needs a revision, not a rethink, and no split.

## Checked

- The revised plan and eval rows r1 to r6, and round 1's verdict.
- src/kmctl/pin.py `hand_off`, `handoff_pin` and `pinned`. `pinned()` reads KMCTL_PINNED, and `handoff_pin` returns None when it is set.
- `git show v0.8.0:src/kmctl/__init__.py` `main`, and `git tag --contains 9801f41b`. v0.7.0 and v0.8.0 both ship the hand-off, which runs before `app()`, and the uvx path is online for every verb but briefing.
- ADR 0026: it says "Before any command" and records that the CI action sets KMCTL_PINNED=1 to run its own copy.
- src/kmctl/summary.py: `changed_concepts` and `ack`. ack writes to `.okf/summary.md`'s front matter, and git then sees the summary as changed.
- apm/claude/.apm/hooks/hooks.json: the guard pattern the plan copies.

## Findings

- p1 (resolved): the copy on PATH runs the nudge itself, and r2 tests that a pinned project never calls uvx.
- p2 (open, premise): copies on PATH with the hand-off but without the verb (v0.7.0, v0.8.0) never produce a usage error. They start uvx after every matching tool call. Setting KMCTL_PINNED=1 in the hook command fixes this for every copy, and r2's missing-verb case should test that.

## Notes

Freshness rule drift between the copy on PATH and the pin is not a real risk. The rule is git-based ("a concept changed after the summary's last commit or edit"), and ack resolves it by changing summary.md itself, so any copy reads an ack the same way. At worst a newer or older rule disagrees about an edge-case path, and the nudge is advisory and never blocks.

On ADR 0026: it says the hand-off runs "before any command", and it already names one exception for briefing and one escape (KMCTL_PINNED in CI). With the KMCTL_PINNED fix, the nudge uses the escape ADR 0026 already records. Still, the new decision that supersedes ADR 0004 should say in one line that the nudge hook runs the copy on PATH and why. If the plan keeps a verb exemption inside hand_off as well, ADR 0026 and the `hand_off` docstring need that note too. This is a revision detail, not a separate finding.
