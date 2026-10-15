---
type: verdict
title: 'Verdict: new-concept-freshness plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of new-concept-freshness: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T17:21:08+00:00'
slug: new-concept-freshness
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works. review due already reads both fields, the strict validator accepts them, and the code to change is small and in one place. Two parts of the contract need settling before the build: what "tracked" means for --source (no git, files not yet committed, matching how review due resolves paths), and whether --source applies to handoffs, which review due never checks for sources. Neither needs a rethink, and one ticket is the right size.

## Checked

- Sources shape: `field(meta, "sources[].resource")` reads both plain strings and `{resource: ...}` mappings (okf.py `_STRING_ITEMS`), but the vendored strict validator warns "`sources[i]` must be a mapping" on a plain string (tests/vendor/okf/okf_validate.py:316), so with --strict it must be written as `- resource: PATH`. Row r4 catches this, so it is not a finding.
- Tracked check without git: review_due.py `_history_skipped` and `ls-files -z`; sources are skipped completely when history is skipped (see p1).
- Path resolution: `_resolve` order and the leading-`/` rule (see p1).
- Months: the plan defines `m` as months, not minutes, and help text can say so. timedelta has no months, so the build needs calendar math (clamping to the month's last day). That is a build detail.
- Timestamp format: handoffs write `%Y-%m-%dT%H:%M:%SZ`. YAML loads it as a datetime, `as_datetime` normalises it to UTC, and the validator's RFC3339 check passes it today. Using the same format for both new forms is safe.
- Verified first: kmctl writes no `verified` entry, and the okf-bundle rule says only a person adds one, so a new concept is due as "unverified" until someone verifies it, and only then can "source changed" fire. The plan's done-when and row r3 already verify before committing, so the test is sound. The feature's value comes after a person's first verify, which matches ADR 0006.
- Budget: the kmctl block is not part of the briefing's WORD_BUDGET (briefing.py does not include scaffold.BLOCK), and no test caps the block's length. init-claude-md-always changes `_write_block` and the import logic but not the duties list, so adding one duty line is a small merge.

## Findings

- p1: "tracked" is undefined for no-git, shallow and not-yet-committed paths, and the check must resolve paths as review due does.
- p2: --source on handoff writes a field review due never reads, and the --key update rewrites it.

## Notes

No spike needed. Each question here is a choice about the contract, not about behaviour.
