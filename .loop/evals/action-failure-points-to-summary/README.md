---
type: eval
title: 'Eval: action-failure-points-to-summary'
description: 'Definition of done for action-failure-points-to-summary: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T13:10:52+00:00'
slug: action-failure-points-to-summary
signoff:
  signer: delegated:jasperginn@gmail.com/agent
  hash: 6b10f3dbc2b4d8dd7ba717063cd909b55f67a024e116afeecf2b21e8da6ebfd7
  at: '2026-11-26T13:10:52+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: When kmctl check fails, action/knowledge-ci.sh prints a GitHub ::error line to stdout that names kmctl check, says the reasons are on the run's summary page, and gives the link GITHUB_SERVER_URL/GITHUB_REPOSITORY/actions/runs/GITHUB_RUN_ID/attempts/GITHUB_RUN_ATTEMPT; the script still exits nonzero.
  Fails when: a run with a broken bundle and the GITHUB_* run variables set prints no ::error line, the line does not name kmctl check, or the link is missing or wrong, or the script exits 0
- r2: When kmctl review due crashes, the script prints the same kind of ::error line naming kmctl review due, with the same link.
  Fails when: a run whose kmctl review due crashes prints no ::error line naming kmctl review due, or the link is missing
- r3: A passing run prints no ::error line, and outside GitHub (no GITHUB_SERVER_URL, GITHUB_REPOSITORY or GITHUB_RUN_ID) a failing run still prints the ::error line, pointing at the summary without a broken link.
  Fails when: a passing run prints ::error, or a failing run without the run variables prints a link with empty parts or no ::error line
- r4: The how-to that installs the Action says a failed check names the failed command in the log and links the summary page.
  Fails when: docs/how-to/install-the-plugin-and-the-ci-action.md does not mention the summary link in the log
