---
type: verdict
title: 'Verdict: schema-verbs reviewer round 1'
description: 'reviewer verdict for round 1 of schema-verbs: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T05:21:50+00:00'
slug: schema-verbs
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `src/kmctl/kinds.py` holds one table of 15 kinds. `kmctl schema` lists them, prints valid draft 2020-12 schemas, and refuses an unknown kind with the list. The writers (`concepts.py`, `docs.py`, `scaffold.py`, `supersede.py`) import their skeletons, manifesto sections and status values from it. The briefing names the verb within its budget. One non-blocking design gap remains: a superseded decision, which kmctl itself writes, does not match the decision schema's fixed section list.

## Checked

- Gates, run by me in the worktree: `uv run pytest -q` gave 355 passed, 10 deselected (the integration tier). `uv run ruff check` gave all checks passed. `uv run ruff format --check` gave 71 files already formatted. I did not run the network integration gate.
- Eval rows: each row's command passed (r1 2 passed, r2 23, r3 2, r4 1 plus test_briefing, r6 1, r5 the full suite). I read each test against its fails_when. r1 checks the exact set of 15 kinds, and that the refusal exits 1 with every kind on stderr and nothing on stdout. r2 runs `check_schema`, walks every property path, nested ones included, against ALLOWED_FIELDS and requires a description on each, and checks that no-front-matter kinds reject `{"title": ...}` and that the index needs `okf_version` and rejects anything else. r3 runs init, every `kmctl new` kind with `--stale-after`, and `--source` on all but handoff, plus all four doc types. It validates the front matter and checks the sections for equality, pattern or last-is-Depicts, and covers the repo's own `overview.md`. r4 checks the help wording and the briefing. r6 walks the AST of every other module for SKELETONS, the skeleton lists, the status words, `architecture`/`Depicts` and the manifesto headings, and checks the four imports. Each test would fail if its behaviour broke.
- Code read in full: kinds.py, the CLI command, and the edits to concepts, docs, scaffold, supersede and briefing. `_cited` and `_sub_path` resolve every path through ALLOWED_FIELDS, so a field that does not exist would raise. `jsonschema` is a dev dependency only; the runtime does not import it.
- Consistency: the architecture overview's diagram, verb table and Depicts section now include `kmctl schema` and `kinds.py`. docs/reference/commands.md documents the command, its body forms and its exit code. The help makes no claim that `kmctl check` or the validator enforces the schema. The `metavar="decision"` example follows the CLI's existing convention.
- I ran this repo's own `.okf/` documents through the test's `_check`. That produced finding f1 and the manifesto note below.

## Findings

- f1 (design, non-blocking): `kmctl decision supersede` appends `## Correction, DATE` sections to a decision, but the decision's `x-kmctl-sections` is a fixed list of three. A record kmctl itself wrote then fails its kind's schema, which goes against the "it is what kmctl writes" claim in the help and the docs. The plan's done list does not cover supersede output, so this does not break the contract. A plain fix is enough: either a body form that allows trailing Correction sections, or a sentence in `_body_text`, the help and the docs saying superseded records add dated Correction sections after the fixed list.

## Notes

The repo's own manifesto has different sections (Where knowledge lives, Parts, Invariants, Values, Out of scope for now). kmctl init writes the three-section skeleton and the operator owns the rest, so the schema's "these sections, in this order" describes the skeleton, not every manifesto. The schema's description could say so. I am not raising this as a finding.
