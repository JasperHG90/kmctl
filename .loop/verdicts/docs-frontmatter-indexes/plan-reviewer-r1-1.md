---
type: verdict
title: 'Verdict: docs-frontmatter-indexes plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of docs-frontmatter-indexes: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T16:44:17+00:00'
slug: docs-frontmatter-indexes
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds and nothing needs rethinking, but three gaps would break the build or its meaning: the source-changed rule has no baseline for docs pages that are never verified (p1), the pre-commit hook row cannot run as its command is written (p2), and the plan's own reason for the root warning is undercut by making a missing folder index an error on upgrade (p3). The ticket is one coherent change; I do not think it needs splitting.

## Checked

- The plan lists no risks ('none') and there are no spikes for this slug.
- `src/kmctl/review_due.py`: returns early without `.okf/`; the source-changed reason needs a verified date (line 179); ids come from the path relative to `.okf/`.
- `src/kmctl/okf.py`: `field` and `ALLOWED_FIELDS` already allow description, stale_after, verified and sources, so no new field names are needed; `source_candidates` resolves from the concept folder, the bundle, then the repo root, which works for docs pages via the repo root.
- `src/kmctl/checks.py`: `Finding.level` is `Literal["error", "skipped"]`; `check_docs` today requires docs/README.md to list every page.
- `action.yml` and `action/knowledge-ci.sh`: the action installs kmctl from its own ref and pipes `kmctl check` output to the summary, so a warning shows there without extra work.
- `apm/.apm/skills/audit/SKILL.md` keeps only architecture/, decisions/ and practices/ ids, so `docs/` ids from review due do not leak into the audit.
- `pyproject.toml` addopts (`-m "not integration"`), `justfile`, `.pre-commit-config.yaml` and `.loop/config.toml` gates, for r11.
- This repo's docs/: 6 pages in 4 folders, no folder indexes, root README lists each page with a description, as the plan says.

## Findings

- p1: unverified docs pages have no baseline for 'a listed source changed'; review_due only compares against verified.
- p2: r11's pre-commit test needs a tool not installed, a committed copy of the tree and likely the network, and its command would select no tests if marked integration.
- p3: a missing folder index is an error, so an upgrade turns downstream CI red, which contradicts the reason given for making the root finding a warning.

## Notes

Not a finding, but worth a sentence in the plan: today check_docs makes the root index list every page under docs/. After this change only the four Diataxis folders are indexed, so a page directly in docs/ or in another folder (for example docs/guides/) is no longer checked by any index. Decide whether such a page is an error, a warning or allowed. Also, review_due returns early when there is no `.okf/`, so docs pages in a repo without a bundle would not be listed unless that guard moves.
