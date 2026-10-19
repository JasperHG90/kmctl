---
type: plan
title: 'Plan: decision-draft-status'
description: The okf-bundle rule allows a draft decision status, as the schema and OKF v0.2 do, and says how a draft becomes stable.
tags:
- plan
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:29:38+00:00'
slug: decision-draft-status
epic: null
depends_on: []
priority: null
---

# decision-draft-status

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none
<!-- When this ticket carries a finding raised while building another ticket,
replace "none" with that ticket's slug and the finding, in one line (ADR 0001). -->

## Intent

The knowledge rule tells people a decision's `status` is `stable` or
`deprecated`, while the schema (`src/kmctl/kinds.py`, `STATUS_VALUES`, OKF
v0.2 section 5.4) accepts `draft` and `kmctl check` passes it (issue #27).
The operator chose to allow `draft` in the rule. This ticket changes the
Decisions section of the rule so it says `status` is `draft`, `stable` or
`deprecated`, what `draft` is for (a choice written down and awaiting
acceptance, unlike a proposal in `proposals/`, which weighs options), and how
a draft becomes `stable`: once accepted, its `status` changes to `stable` and
a line in `log.md` records it. That status change is the one edit a record
takes besides appended Correction sections and what
`kmctl decision supersede` writes.

Measured: 3 of 3 copies of the rule carry the contradiction
(`apm/claude/.apm/instructions/okf-bundle.instructions.md` line 94,
`apm/antigravity/.apm/instructions/okf-bundle.instructions.md` line 95,
`.claude/rules/okf-bundle.md` line 91); `docs/` has no such wording. A copy of
this repo's `.okf/` with ADR 0030 set to `status: draft` passes
`kmctl check` (exit 0). This repo's 30 decisions are 23 `stable`, 7
`deprecated`, 0 `draft`, so the change fixes guidance, not existing records.

Where the change lands:

- `apm/claude/.apm/instructions/okf-bundle.instructions.md`, the source.
- `apm/antigravity/.apm/instructions/okf-bundle.instructions.md`, regenerated
  by `scripts/sync_antigravity_rules.py` (the pre-commit hook), never edited.
- `.claude/rules/okf-bundle.md`, this repo's own copy. It is not in
  `apm.yml` (those entries come from jasperhg90/skills), so it is edited here,
  with the same sentence.
- `tests/test_apm_package.py`: `OLD_RULES` pins the sha256 of the okf-bundle
  body, changed only by a change an ADR names, so the hash and its comment
  move to the new ADR.
- `new:.okf/decisions/0031-a-decision-record-may-be-draft-until-it-is-accepted.md`,
  written with `kmctl new decision 'A decision record may be draft until it is accepted'`
  (the rule itself asks for a record in the same change), rejecting the
  other route in the issue: refuse `draft` in the schema and send proposed
  choices to `proposals/`.

Outcome: none of the three rule copies still says "`status` is `stable` or
`deprecated`"; each names `draft` and how it becomes `stable`, and
`just lint` and `just test` pass with the new hash.

## Could invalidate this plan

- none
