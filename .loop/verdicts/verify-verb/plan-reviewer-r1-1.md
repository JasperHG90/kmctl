---
type: verdict
title: 'Verdict: verify-verb plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of verify-verb: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T21:24:51+00:00'
slug: verify-verb
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan can work, but as written the verb will not always do what it promises: it can exit 0 and leave the id in kmctl review due. Two gaps cause that. A bare-date `at` loses to a source committed the same day (p1). A verified entry never clears `stale_after passed`, but the new Next: line sends agents to verify for every due reason (p2). Both are revisions, not a rethink. The listed briefing risk is settled by the spikes, and the ADR 0005 and I2 question has a clean answer.

## Checked

- Spike verify-verb/1 (README, stdout, run.json): the worst-case briefing test is at 494/500, and the shortest added hint reaches 505. This supports leaving the briefing as it is.
- Spike verify-verb/2: in a clean tree, `kmctl briefing` prints `State: 24 concepts due for review (kmctl review due)`. The grep exited 0, so the briefing does point at review due, where the Next: line will sit.
- src/kmctl/review_due.py and src/kmctl/okf.py (`as_datetime`, `has_passed`): what makes a concept due and a docs page due, and how dates compare. This is where p1 and p2 come from.
- ADR 0005, ADR 0006, manifesto I2 and I4: ADR 0005 already says "A person, or an agent the person asks, acts on them". I2 bars the audit agent, its skills and the CI action from writing stamps; it does not bar a verb a person asks for. `verified`, `verified[].by` and `verified[].at` are in ALLOWED_FIELDS, and ADR 0022 lets docs pages carry `verified`. So I4 holds, and the new ADR adds to ADR 0005 rather than changing it.
- .claude/rules/cli-interface.md: the plan's Next: lines, refusals on stderr with a fix, `--json`, and the help tests (r8) match it.
- The okf-bundle rule already says only a person adds `verified` with `by: human:<id>`. append_log exists for the log.md line (supersede.py, concepts.py).
- No `verified` entry exists in .okf/ or docs/ today, so the 24-due figure is consistent.
- As told in the briefing, I did not count the sentence about uncommitted edits in the primary checkout against the plan.

## Findings

- p1: a bare `at: today` date is midnight UTC, so a source committed later the same day still marks the id due after verify. Write a datetime and test the same-day case.
- p2: verify does not clear `stale_after passed`, but the Next: line in review due points at verify for every reason. Either extend the verb or narrow the hint, and test the choice.

## Notes

- A `verified` written as a single mapping (okf.py `_SINGLE_MAPPING`) has to become a list when the verb appends to it. That is a build detail for r3, not a plan risk.
- The CI audit agent (action/agent.py) can run shell commands, so it could technically run kmctl verify. Nothing it changes is committed (ADR 0017), and the skill wording "never on an audit verdict alone" covers the rest. No finding.
- One ticket is the right size; no split needed.
