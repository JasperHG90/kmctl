---
type: verdict
title: 'Verdict: schema-verbs plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of schema-verbs: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T17:27:08+00:00'
slug: schema-verbs
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The revision settles all four round 1 findings: one table in kinds.py that the writers read (p2), no-property schemas and a heading pattern for the log (p1), help that claims only "what kmctl writes" (p3), and no --source on handoffs (p4). One gap is left (p5): the architecture kind's body, free sections ending in `## Depicts`, fits none of the three body forms the plan allows, and r3 checks this repo's own architecture page against it. A one-line revision fixes it. The approach holds otherwise and does not need a split.

## Checked

- Rows against done-when: r1 matches lists every kind and unknown kind refused; r2 matches valid draft 2020-12, ALLOWED_FIELDS-only properties with descriptions, and no-front-matter kinds; r3 matches init, new (with --stale-after on every kind, --source on all but handoff) and new doc output, plus this repo's architecture page; r4 matches the help claim and the briefing budget; r6 matches one definition in kinds.py; r5 is the full suite. Every done-when item has a row, and no row goes beyond it.
- Read concepts.py (SKELETONS, _front_matter writes the literal `status: stable`, append_log), docs.py (SKELETONS, no front matter), scaffold.py (_files: root index with okf_version only, log with a dated heading, docs/README.md with no front matter or ## sections, manifesto sections in a string literal; FIRST_BODY matches the decision skeleton), supersede.py (writes `status: deprecated` by regex), okf.py ALLOWED_FIELDS.
- Read .okf/architecture/overview.md: front matter type, title, description, generated (at is a bare date), tags, status; sections The CLI, The plugin, The action, Depicts.
- Ordering: schema-verbs already depends on new-concept-freshness, which depends on init-claude-md-always, so the order is enforced: init-claude-md-always lands first (its branch changes scaffold.py by 87 lines but not the manifesto string or _files), then new-concept-freshness changes _front_matter and the kmctl block, then schema-verbs moves SKELETONS and the manifesto sections into kinds.py. The order matters: schema-verbs' r3 needs --stale-after and --source to exist, and moving the constants first would make both earlier tickets rebase onto the move. Keep it as declared.

## Findings

- p1 resolved: no-front-matter kinds allow no properties, the root index allows only okf_version, and the log is a heading pattern.
- p2 resolved: skeletons, manifesto sections, status values and the architecture type and Depicts move into one table in kinds.py that the writers import; r6 checks it.
- p3 resolved: help says only that the schema is built from kmctl's table and is what kmctl writes; r4 checks it does not claim check or the validator enforce it.
- p4 resolved: r3 excludes --source on handoffs.
- p5 open: the architecture body (free sections, Depicts last) fits none of the plan's three body forms, so r3's check of this repo's architecture page has no form to pass against.

## Notes

- Build detail, not a finding: r6 says status values are defined only in kinds.py, but concepts.py writes `status: stable` and supersede.py writes `status: deprecated` as literals. Either have both read the value from the table, or have the test look for a second definition of the value set, not every use of a word.
- Build detail: after init-claude-md-always, kmctl init also writes CLAUDE.md, AGENTS.md and rule files that are not kinds. r3's "everything kmctl init writes" means the bundle and docs files; the test should name them.
- The round 1 note on PyYAML dates still applies: this repo's architecture page has a bare-date generated.at, so the schema has to accept a date as well as a datetime there.
- No spike is needed.
