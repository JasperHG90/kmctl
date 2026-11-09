---
type: plan
title: 'Plan: real-audits'
description: The agent's report lists what it compared and mismatches only, and the script rejects evidence from files the agent never read.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T14:21:08+00:00'
slug: real-audits
epic: null
depends_on: []
priority: null
---

# real-audits

Relayed from: none

## Intent

A live run of `action/agent.py` on main (2026-10-17) returned 20 `info`
"holds" findings and no drift, after reading five files outside `.okf/`,
and cited lines in files it never opened. Its report shape invites that:
every concept becomes a finding, and nothing checks the evidence.

This ticket changes the report and checks the evidence in code, so any
audit prompt (the three in the follow-up `audit-prompts`) gets it:

- `Report` in `action/agent.py` gains `checked`: one entry per page or
  concept compared, naming what it was compared against, with evidence.
  `findings` are mismatches only: each names the claim (`path:line`), the
  evidence that contradicts it (`path:line`) and a suggested fix. The
  shipped system prompt says a thing that holds goes in `checked`, never in
  `findings`; the default prompt's "holds is info" mapping goes.
- The workspace records every file the agent read (with the line range)
  and every `path:line` a search returned. An output validator sends the
  agent back with `ModelRetry`, naming each bad citation, when a finding or
  `checked` entry cites a line it neither read nor got as a search hit, or
  a line past the file's end. Prompts may, code must.
- `report.md` and the step summary show the checked list after the
  findings; `publish` is unchanged (it counts findings at the threshold).

Measured on that run's transcript: of 61 citations, 18 point at a line the
agent neither read nor got from a search (strict variant: the file read,
or that exact `path:line` a search hit). 10 of the 18 name files it never
touched (`src/kmctl/antigravity.py`, `review_due.py`, `scaffold.py`,
`handoffs.py`, the release workflows). The check would have sent that run
back on 18 of 61 citations; its "holds" for ADRs 0006, 0012, 0015, 0016
and 0018 rest on them.

Done when the offline tests show: a report citing an unread line is sent
back and a corrected one is accepted; `report.md` lists checked entries;
findings carry claim, contradiction and fix.

## Could invalidate this plan

- The validator may trap the agent in retries it cannot leave (it cites a
  line it read through a range, or a search hit it then reformats), using
  up the request cap. Spike: run the validator live on the current repo
  with Gemini Flash and count retries and whether the run finishes.
  Settled by spike:real-audits/2: the run finished in 85 of 200 requests,
  0 of 62 citations rejected, 0 retries. Told its citations are checked,
  the agent read 47 times (was 31) and searched 27 times (was 10). Live
  runs never hit a retry, so the offline tests must cover recovery after
  a rejection; PydanticAI 2.57 sets output retries with
  `retries={"output": N}`, not `output_retries`.
