---
type: plan
title: 'Plan: first-decision-detect'
description: kmctl init and update write the first decision only when .okf/decisions/ holds no decision record, not when no record has its title.
tags:
- plan
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:29:26+00:00'
slug: first-decision-detect
epic: null
depends_on: []
priority: null
---

# first-decision-detect

Relayed from: none

## Intent

`kmctl init` and `kmctl update` (the same command, ADR 0011's 2026-10-16
correction) write the decision "Keep project knowledge in an OKF bundle"
when no record in `.okf/decisions/` has that title, ignoring an `ADR N:`
prefix (`_has_first_decision` and `_write_first_decision` in
`src/kmctl/scaffold.py`, called on every `scaffold()`). A repository that
records the same choice under another title, or moves an existing decision
log into `.okf/decisions/`, gets a new copy on every run, numbered after its
own records (issue #26). Measured on main: `kmctl init --json` on a copy of
this repository's `.okf/` (30 decisions, none with that title) creates
a duplicate record, 0031-keep-project-knowledge-in-an-okf-bundle.md, and updates
the kept `.okf/log.md` and `.okf/decisions/index.md`.

The change: kmctl writes the first decision only when `.okf/decisions/` is
missing or holds no decision record, meaning no `*.md` file other than
`index.md`. It no longer reads titles, so `_has_first_decision` and the title
match go. A record whose front matter does not parse still counts, so a
broken file never brings the duplicate back. A fresh bundle still starts
with `0001`, and running init twice still changes nothing.

Rejected: a tag kmctl looks for. A migrated log or a record written by hand
does not carry it, so it fixes only the case kmctl wrote itself, and it adds
a field to keep. Keeping the title rule beside the empty-folder rule adds
nothing, because a record with that title already makes the folder non-empty.

The words that describe the rule change with it: the `scaffold()` docstring
and `ScaffoldResult`'s, the `kmctl init` epilog in `src/kmctl/__init__.py`,
and `docs/reference/commands.md` ("when no record in `.okf/decisions/` has
that title"). ADR 0011
(`.okf/decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md`)
chose the title rule in its Decision ("when no record has that title"), so it
gets a dated Correction that states the new rule, cites issue #26 and names
the rejected tag; `.okf/log.md` gets its line. The manifesto's first-decision
line (`.okf/manifesto.md`) and `.okf/summary.md` are checked and changed only
if they state the title rule.

Tests in `tests/test_init.py`:

- New: init over a bundle whose `.okf/decisions/` holds records with other
  titles writes no decision and leaves every file in `.okf/` byte for byte.
  This is the measured case above: 0 records created instead of `0031`.
- New: init over a `.okf/decisions/` holding only `index.md` writes `0001`.
- `test_init_first_decision_not_written_twice`,
  `test_init_reports_kept_files_it_changed_as_updated` and
  `test_init_human_output_names_why_each_file_was_updated` copy this
  repository's bundle and expect the first decision written into it. Under
  the new rule they must empty `.okf/decisions/` of records first (keeping
  its index entries consistent) so they still test writing into a kept
  bundle. `test_init_first_decision_kept_when_title_exists` keeps passing and
  is renamed for what it now shows: records present, nothing written.

Done when that new test shows 0 records written over this repository's
bundle, and `just lint`, `just test` and `just integration` pass.

## Could invalidate this plan

- none
