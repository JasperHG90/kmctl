---
type: verdict
title: 'Verdict: docs-frontmatter-indexes plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of docs-frontmatter-indexes: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T16:47:31+00:00'
slug: docs-frontmatter-indexes
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three round 1 findings are settled and I found no new risk that could break the plan. The plan passes.

## Checked

- The one listed risk, prek running a `language: python` hook from a local repo pinned by sha, is settled by spike:docs-frontmatter-indexes/1. Its README, stdout and run.json show prek 0.5.5 installed and ran kmctl-check from a clone pinned by sha, exit 0, in about 2 s, and `args` reached the command. The spike only had warm caches and no docs/ in the consumer repo, but those are build details, not risks to the approach.
- p1: the plan and r6 now name the page's own last commit as the baseline when there is no `verified`, and run review due without `.okf/`. `review_due` already reads commit times with `git log -1 --format=%cI` and skips history in shallow clones (`_history_skipped`), so the same path covers the page's own commit.
- p2: r11 splits into an offline shape check and a test marked `integration`. The `-m integration` given on the command line overrides addopts `-m "not integration"`, and the integration gate (`uv run pytest -m integration` in `.loop/config.toml`) picks up the new test.
- p3: the operator chose an error for a missing folder index. The plan states the cost (downstream CI fails once with the `kmctl check --fix` fix line) and puts it in the ADR and commands.md. It is no longer an unstated contradiction.
- The round 1 note on pages outside the four Diataxis folders is answered: they must still be listed in docs/README.md (r2).

## Findings

- p1: resolved by the page's-last-commit baseline and the no-`.okf/` path in r6.
- p2: resolved by the offline/integration split in r11, backed by the spike.
- p3: resolved as an operator choice, stated with its cost and fix line.

## Notes

None of these is a finding. A hand-written folder `README.md` gets only a warning, so in that folder no index is checked against its pages. The plan accepts this to keep user text safe.
