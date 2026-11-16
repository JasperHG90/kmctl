---
type: verdict
title: 'Verdict: package-direction reviewer round 1'
description: 'reviewer verdict for round 1 of package-direction: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T11:54:57+00:00'
slug: package-direction
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. ADR 0046 records the direction rule in the operator's words, with the history scan as the case that settled it and the rejected alternative. It links ADR 0043 and leaves it unchanged. The root README names each package's direction and links the decision, and AGENTS.md (CLAUDE.md) routes to it. The gates and both eval rows pass on my own stamp. One wording problem remains, and a plain fix will do: the decision talks about the unbuilt history scan as if it exists and is sure to be built.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration, eval-row r1 and eval-row r2 all pass, "stamp green: d229fa5a2ab35353d8a1d3925ab0de6f007617ee099fceb60a90f5d894559347".
- `prek run --files` on the changed files: `kmctl check --fix`, ruff check and format, and `okf validate --strict` pass.
- Row r1: the three `-k direction` tests cover each part of fails_when. A missing 0046 file makes the module-level `next(glob)` raise, so collection fails. Off-schema front matter fails the jsonschema validation. Wrong sections fail the skeleton comparison. Either bolded direction missing from the Decision section fails. A missing 0043 link fails. Each README entry's direction phrase is checked through `_root_entry`, the README link is resolved against the decision's path, and the CLAUDE.md row must hold both the label and the path.
- Row r2: covered by the full test_readmes.py run and the frontmatter test, and kmctl check passed separately.
- Decision accuracy: `kmctl review due` and `kmctl new` exist. The `/audit` skill in packages/kmctl/apm reviews architecture, decision and practice pages starting from `kmctl review due`. kmaudit's description matches ADR 0043. No history-scan code or skill exists in packages/kmctl, which led to f1.
- Summary trims: the body drops "and people review them" (review is still reachable through the audit-pipeline link) and "Work in flight lives in `.loop/`" (CLAUDE.md's routing table already points to `.loop/`). Nothing load-bearing is lost.

## Findings

- f1: line 38 lists "the history scan for missing decisions" among what kmctl does today, and line 55 says it "is built in kmctl, as a command ... and a skill". The scan is not built, and decision-gaps-measure exists to decide whether to build it. Reword both lines conditionally, for example "a history scan for missing decisions, if built, goes in kmctl" and "The history scan for missing decisions, if built, belongs in kmctl". The placement still counts as the case that settled the rule. Non-blocking because the fix is wording only.

## Notes

The new summary line "kmctl works from code to knowledge, kmaudit back" is terse. It reads fine with the ADR link beside it.
