---
type: verdict
title: 'Verdict: okf-summary-holistic reviewer round 1'
description: 'reviewer verdict for round 1 of okf-summary-holistic: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T22:34:46+00:00'
slug: okf-summary-holistic
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `SUMMARY_SECTIONS` and `SUMMARY_PROMPTS` now hold the four reader-facing sections, and no prompt asks for a link per decision. The block's duty, `SUMMARY_LINE`, all three copies of the okf-bundle rule and `docs/reference/commands.md` say the summary distils the knowledge and the indexes list the concepts. ADR 0027 has a Correction that names the new sections and says why. This repository's summary reads as one view of the project: what kmctl is for, how its four parts fit and how an agent reads in layers, five principles with their reasons and cited records, and where the work stands. Every claim I checked matches the bundle. One part of the design, handoffs, is missing. That is non-blocking, so the verdict is fix.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree myself. Lint, format, tests and integration passed, and so did rows r1, r2, r3 and r5. Result: "stamp green: d4d82a747bc7a23988756031b8edbdb2fbbe43fc589eb80b12270d8a334a38a3". `kmctl check --path .` passes. The summary body is 491 words.
- r1: `test_init_writes_the_summary_sections` asserts that the headings equal the four sections in order, that each prompt line is the one in `SUMMARY_PROMPTS`, and that no prompt matches `(link|list)\w* each`. It also asserts the "never one bullet per decision" wording. The schema test asserts that `x-kmctl-sections` equals the four. Both fail when a section is renamed, reordered or missing, or when a prompt asks for a link per decision.
- r2: `test_guidance_says_the_summary_distils_the_knowledge` reads the block's duty line and the four guidance files from disk. It asserts the distil wording and "the indexes list the concepts" in each, that none says "theme by theme", and that commands.md names the new sections and drops the old ones. It fails if any copy goes stale.
- r3: the single-decision-link check counts top-level bullets per section and fails when most of them carry one `decisions/` link each. A separate test pins how that helper behaves on known input, so the check cannot pass by counting nothing. The word limit and link resolution are asserted elsewhere in the same `-k this_repository` selection.
- r4 (judgment): I read the summary against the manifesto, `architecture/overview.md` and the cited ADRs.
  - "The CLI ... alone writes knowledge" matches overview ("the only part that writes knowledge").
  - "Skills only route to verbs" matches ADR 0001 ("skills route to CLI verbs instead of carrying logic") and the manifesto ("Skills route; kmctl decides and writes").
  - "One SessionStart hook that never blocks" matches ADR 0004. "Rules where the briefing alone left too few records written" matches ADR 0002's 2026-10-15 correction and ADR 0011.
  - "Antigravity also relays okf's Stop check" matches ADR 0018 and I1.
  - Two extension fields, `handoff_key` and `checked`, and no `covers` field, match I4 and ADRs 0006, 0009 and 0027. "Commit order" is ADR 0027's rule for the summary.
  - "Only a person verifies" matches ADR 0023, and "ack is no review" matches ADR 0027.
  - "The CI audit takes any provider and never runs beside a GitHub token" matches ADR 0017 (`--model` takes any provider; the script refuses to start when `GH_TOKEN`/`GITHUB_TOKEN` is set, and only the publish job gets the token).
  - The package version and APM-owns/kmctl-patches claims match ADRs 0014, 0020 and 0021. The release and template-tag claims match ADRs 0012 and 0025, and the pin hand-off matches ADR 0026.
  - "I1, I3 and I4 enforced; I2 planned" matches the manifesto's statuses.
  - "No practices, proposals or prototypes" holds: those folders do not exist. "Many concepts have no verified entry" holds: `kmctl review due` lists them as unverified.
  - The in-flight nudge is the `okf-summary-nudge` ticket, which is at stage ready in the primary checkout.
  - No section lists one decision per bullet. Each principle cites two or three records together, and the page sends readers to the decision index for the full list.
- Consistency: grep finds no "theme by theme" or the old section names left outside `.loop/` and ADR 0027's original body, which the Correction amends as the repo's convention requires. The `kinds.py` purpose, the `summary.py` docstring, `.okf/index.md`, `decisions/index.md`, `log.md` and the okf-bundle rule hash in `tests/test_apm_package.py`, whose comment cites the correction, all agree with the change.

## Findings

- f1 (docs, non-blocking): handoffs are a part of the design, a bundle section with two skills (manifesto Parts, ADR 0008), but the summary never says what they are. Row r4 counts a missing part of the design as a failure. The fix is a clause; it does not need another review.

## Notes

- "Where it stands" names one specific in-flight ticket (the summary nudge). That line will go stale once the ticket lands. The ack and review-due rule will catch it, so I raise no finding.
