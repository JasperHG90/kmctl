---
type: verdict
title: 'Verdict: link-check plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of link-check: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:19:31+00:00'
slug: link-check
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round-1 findings are resolved. The plan now defines how `/` links resolve in docs/ and in .okf/, and it leaves in-bundle .okf/ links to the validator, which warns on them as OKF §6.1 requires. Nothing else I found could break the plan.

## Checked

- Read the revised plan, the round-1 verdict, the empty eval and the knowledge-check plan. knowledge-check gives link-check general link checking and a shared `--json` findings list, which this plan uses.
- OKF SPEC §6.1 (0.10.1): `/` links are bundle-relative and recommended; consumers MUST tolerate broken links "in the bundle". Links that leave the bundle are not concept links, so failing on them does not go against the spec.
- okf_validate.py `check_links`: it checks only `.md` targets, resolves `/` from the bundle root, and warns. For a `.md` link that leaves the bundle it compares the raw string to bundle files, so it also warns on those. Non-`.md` targets such as `../src/x.py` go unchecked.
- Current .okf/ links are all relative and inside the bundle; there is no docs/ folder or site generator config yet.

## Findings

- p1: resolved. `/` resolution is defined for both trees.
- p2: resolved. In-bundle .okf/ links are the validator's; kmctl fails only on links outside its coverage.

## Notes

- The Intent says the validator does not cover links that leave the bundle. It does warn on `.md` ones (see Checked), so for those kmctl fails where the validator warns. This is a small, deliberate overlap and does not break the plan.
- Resolving docs/ `/` links from the repo root follows GitHub. A repo that publishes docs/ through a site generator, where `/` means the site root, would get false failures. Worth one sentence in the help text, not a plan change.
- No spike is needed. One ticket is the right size.
