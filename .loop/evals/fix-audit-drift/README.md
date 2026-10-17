---
type: eval
title: 'Eval: fix-audit-drift'
description: 'Definition of done for fix-audit-drift: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:48:20+00:00'
slug: fix-audit-drift
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: dcb7fd4932a7370e89702a30cd7bb1896732809e376f84a03f8deaa241036be0
  at: '2026-10-17T18:48:20+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The docs and the bundle stay valid after the fixes: kmctl check passes on the repository.
  Fails when: kmctl check reports a broken link, index or schema after the change
- r2: kmctl review due's and kmctl briefing's help say what the commands do now: review due lists docs/ pages as well as .okf/ concepts, and the commands reference quotes the help as the CLI prints it.
  Fails when: review due's help still says it lists only .okf/ concepts, or the reference and the help disagree
- r3 (judgment): The commit message lists every one of the 35 findings (spikes 2 to 4) as fixed, naming the changed file, or not real, with the evidence; decisions change only through Correction sections, their index lines through a note, and every touched concept has a .okf/log.md line.
  Fails when: a finding is missing from the list, a fix is claimed for an unchanged file, a decision's body or description is rewritten, or a touched concept has no log line
- r4 (judgment): The three audits ran once more on the result; any of the 35 that came back was checked again and fixed or recorded as not real, and new findings went to a follow-up stub.
  Fails when: the rerun is missing, a returning finding is left unanswered, or a new finding is fixed in this ticket instead of a stub
