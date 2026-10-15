---
type: verdict
title: 'Verdict: schema-verbs plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of schema-verbs: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T17:24:52+00:00'
slug: schema-verbs
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds for the five concepts kmctl new writes: their type, front matter and sections all come from SKELETONS, _front_matter and ALLOWED_FIELDS. The plan breaks on the other kinds. Docs pages, the indexes and the log have no front matter and no fixed sections, so their schemas state nothing or invent things (p1). Several values the schema must give (status values, required fields, the manifesto's and architecture pages' sections) are not in kmctl's code, so "cannot drift" is not true for them (p2). The help claims kmctl check enforces the schema, and it does not (p3). The eval asks for --source on handoffs, which the dependency refuses (p4). All four can be fixed by revising the plan, not rethinking it. The plan lists no risks; these four should have been there.

## Checked

- Ran `loopctl schema --help` to compare the shape: a list with no name, one schema per name, help that says where it comes from. The plan copies that pattern.
- Read src/kmctl/okf.py (ALLOWED_FIELDS: names and citations only, no required set or values), concepts.py (SKELETONS, _front_matter: status stable only for decisions, stale_after only for handoffs, section index written as '# Name' with no front matter, append_log writing dated ## headings), docs.py (no front matter on pages), scaffold.py (manifesto sections in a string literal, root index with okf_version only, log with a dated heading), checks.py (check_okf checks only indexes), supersede.py (deprecated), briefing.py (WORD_BUDGET 600, verb line at lines 33-35).
- Read tests/vendor/okf/okf_validate.py: STATUS_VALUES, RECOMMENDED, the rule that index.md and log.md carry no front matter and the root index only okf_version, and that the only per-type check is for Attested Computation.
- Compared with the repo's own bundle: .okf/manifesto.md has no 'What this is for' section; .okf/architecture/overview.md has type architecture, status stable and '## Depicts' last, and these come only from repo_rules/diagrams-stay-current.md.
- Read new-concept-freshness's plan for --stale-after and --source: handoff refuses --source.
- pyproject.toml: no JSON Schema validator. jsonschema is not in uv.lock; adding it as a dev dependency with `uv add --dev jsonschema` fits the dependency-choice rule and is not a risk.

## Findings

- p1: the no-front-matter, no-fixed-section kinds (docs pages, docs index, section index, log, root index) have no stated schema content, and the log's dated headings cannot match a fixed section list.
- p2: status values, required fields, the manifesto skeleton and the architecture Depicts rule are not in kmctl's code, so the schema would hard-code them.
- p3: the help claims kmctl check and the strict validator enforce the schema; neither does.
- p4: r3 asks for --source on handoffs, which the dependency refuses.

## Notes

- One build detail, not a finding: PyYAML parses unquoted timestamps (generated.at, stale_after) and bare dates as datetime and date objects, so a test that checks front matter against a schema with "type: string, format: date-time" has to choose how to turn them into JSON first. The schema should say what it accepts (this repo's own pages use bare dates in generated.at).
- The briefing has 74 words of room under the budget; one verb clause fits.
- No spike is needed. Each finding is answered by reading the code, and the fixes are choices the plan has to make.
