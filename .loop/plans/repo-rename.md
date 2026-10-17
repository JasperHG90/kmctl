---
type: plan
title: 'Plan: repo-rename'
description: Name the renamed repository JasperHG90/kmctl everywhere kmctl points users, while still recognising installs made from the old name.
tags:
- plan
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:48:53+00:00'
slug: repo-rename
epic: null
depends_on: []
priority: null
---

# repo-rename

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

The GitHub repository was renamed from `JasperHG90/Knowledge-management` to
`JasperHG90/kmctl`. GitHub redirects the old name for now, but the redirect
ends if anything is ever created under it. Everything kmctl tells a user to
run or write names the new repository:

- `src/kmctl/plugin.py`: `DEFAULT_SOURCE` (the `apm.yml` entry patch and
  doctor suggest) and the install line in `HOOK_COMMAND`; the same line in
  `src/kmctl/antigravity.py`'s hook and its issues link. The generated
  `apm/claude/.apm/hooks/hooks.json`, `apm/antigravity/.apm/hooks/hooks.json`
  and the comment in `apm/apm.yml` follow.
- `scripts/release.py`: the patterns that move the docs' version pins.
- `README.md` and every page under `docs/` that names the repository.
- The tests that name it.

Installs made from the old name keep working: the lock names the package
`kmctl` at `virtual_path: apm` whichever URL installed it, and that is what
`kmctl_package` matches. The two checks that do read the URL, `_old_layout`
(a v0.3.0-or-older lock) and `_names_old_package` (the ADR 0013 string
entry), accept both names, with a test for each. The ADRs keep the old name:
they record what was decided at the time.

The template repository `/home/vscode/kmctl-starter` names the old
repository in four files; it is a separate git repository, updated and
committed there alongside this ticket.

The outcome: outside `.okf/decisions/` and `.loop/`, no tracked file names
`JasperHG90/Knowledge-management` except the constants that recognise old
installs, and an install from the old name is still found by patch and
doctor.

## Could invalidate this plan

- APM records a package installed from the new URL differently, so kmctl
  stops finding it, or finds an old-name install as a different package.
  Holds: the lock names it `kmctl` at `apm` from the new URL too, and
  `kmctl_package` matches name and path, spike:repo-rename/1.
