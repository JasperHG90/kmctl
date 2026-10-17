---
type: eval
title: 'Eval: real-audits'
description: 'Definition of done for real-audits: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T16:27:38+00:00'
slug: real-audits
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: 4696344537dd8e17a2d54dde631097af21ce9f7f9554895ab330132df73b10fd
  at: '2026-10-17T16:27:38+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Report holds checked entries (subject, compared against, evidence) and findings that each carry a claim path:line, the path:line evidence that contradicts it and a suggested fix; report.md and the step summary list the findings and then the checked entries.
  Fails when: report.json lacks checked, a finding lacks claim, contradicted_by or fix, or report.md leaves out a checked entry report.json holds
- r2: When the agent's output cites a path:line it neither read (inside the line range read_file returned) nor got as a search hit, or a line past the file's end, the agent is sent back with a message naming each bad citation; a corrected output is then accepted and written.
  Fails when: an output citing an unread line, a line outside the range read or a line past the end is written to report.json, the retry message does not name the citation, or the corrected output is not accepted
- r3: An agent that keeps citing unread lines stops after the output retry limit with exit 1 and a message saying its citations could not be checked, and writes no report.json.
  Fails when: the run loops past the limit, exits 0, or writes report.json with unchecked citations
- r4: The shipped system and default prompts say a thing that holds goes in checked, never in findings, and that citations are checked; the default prompt no longer maps holds to info.
  Fails when: either prompt still tells the agent to make a finding for something that holds
- r5 (judgment): ADR 0017 (a correction), the how-to's section on the CI action and the architecture overview describe the checked list and the evidence check.
  Fails when: a reader of the docs would expect info findings for things that hold, or not know citations are checked
