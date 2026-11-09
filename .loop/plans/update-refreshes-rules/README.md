---
type: plan
title: 'Plan: update-refreshes-rules'
description: Add kmctl update as an alias of init, and have init overwrite the four shipped knowledge rules on every run.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:56:32+00:00'
slug: update-refreshes-rules
epic: null
depends_on: []
priority: null
---

# update-refreshes-rules

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

After upgrading kmctl, a user re-runs one command and gets the current
knowledge rules. Today `kmctl init` keeps any `.claude/rules/` file that
exists (`_write_rules` in `src/kmctl/scaffold.py`), so upgrades never reach
the four rules kmctl ships (`okf-bundle`, `docs-layout`,
`diagrams-stay-current`, `manifesto-invariants`), and there is no `update`
verb, which users look for.

Changes:

- `kmctl update` is an alias of `kmctl init`: same options, same behaviour,
  same `--json` shape. Both appear in `kmctl --help`.
- init (and so update) overwrites each of the four rule files with the
  packaged copy on every run. A file whose content already matches is left
  as is and listed in `skipped`; a file that differed is rewritten and
  listed in `updated`; a missing one is `created`. Only those four names are
  touched; other files in `.claude/rules/` are never read or written. No
  hash tracking of user edits (the operator rejected it).
- A new ADR records that kmctl owns those four files and supersedes the
  "an existing file of the same name is kept" part of ADR 0011
  (`.okf/decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md`),
  via `kmctl decision supersede` or an appended correction, whichever the
  record rules require.
- `kmctl init --help`, `docs/reference/commands.md`, `README.md` and
  `docs/tutorials/get-started-with-kmctl.md` say the rules are replaced and
  name `kmctl update`.

Outcome: in a repo where `kmctl init` ran and `.claude/rules/okf-bundle.md`
was then edited, `kmctl update --json` lists it in `updated` and the file
equals `src/kmctl/repo_rules/okf-bundle.md` afterwards; a second run lists
it in `skipped`.

## Could invalidate this plan

- none
