---
type: prototype
title: "Token costs"
description: "What kmctl costs to use, measured from 141 real agent runs on this repository: claims extraction $0.0068 per section and check writing $0.0081 per claim on Claude Haiku 5.5, about $11 for a full audit of this bundle from scratch, and about 3,400 tokens of context per session for the briefing and knowledge rules."
tags: [prototype, audit, cost]
generated:
  by: claude-opus/5.5
  at: 2026-11-12T14:00:00Z
verified:
  - by: human:jasper
    at: 2026-11-27T20:41:27Z
---

# Token costs

## Question

What does it cost, in tokens and dollars, to use kmctl: for the audit
pipeline (claims extraction and check writing), and for the context kmctl
adds to a session in which an agent writes docs?

## Method

`measure.py` reads the subagent transcripts of one Claude Code session
(`~/.claude/projects/<project>/<session>/subagents/`), keeps the claims
extractor and check writer runs, and for each distinct API message sums
fresh input, cache writes (5-minute and 1-hour apart), cache reads and
output. It prices each message at its own model and prompt-size tier, and
reads the work each agent reported (sections stored, or checks plus
reasons). It writes `agents.csv`, counts only, with no transcript text.

```
uv run python .okf/prototypes/token-costs/measure.py ~/.claude/projects/<project>/<session>/subagents
```

Prices are the Claude API list prices on 2026-11-12
(<https://platform.claude.com/docs/en/about-claude/pricing>). Claude Haiku
5.5, which ran 9,225 of the 9,931 agent messages: $0.10 input, $0.125
5-minute cache write, $0.20 1-hour cache write, $0.01 cache read and $0.50
output per million tokens, five times that for a prompt over 100,000
tokens. Characters of context are counted from the files and turned into
tokens at four characters a token, the estimate invariant I3 uses.

The runs are those of 2026-11-11 and 2026-11-12 on this repository: the
first full audit, two re-extractions after doc edits, and the check-writing
rounds that followed.

## Results

| Agent | Runs | Work | Cache write | Cache read | Output | Cost |
|---|---|---|---|---|---|---|
| Claims extractor | 34 | 390 sections, 2,884 claims | 9,447 per section | 35,768 per section | 2,905 per section | $0.0068 per section ($2.65) |
| Check writer | 107 | 2,531 claims answered | 5,418 per claim | 118,851 per claim | 1,076 per claim | $0.0081 per claim ($20.60) |

Fresh input is one or two tokens per unit: everything else is served from
the prompt cache.

- **A full audit of this bundle from scratch** (207 sections, 1,182
  checkable claims): 207 × $0.0068 + 1,182 × $0.0081 = about $11 on Haiku
  5.5. Rerunning stored checks (`kmctl audit checks run`) costs nothing:
  no model runs.
- **Long prompts dominate the writer's bill.** 1,589 of the writer's 2,858
  messages (56%) had prompts over 100,000 tokens, which Haiku 5.5 bills at
  five times the base rates; for the extractor, 56 of 234 (24%). A writer
  run grows past 100K as its rounds pile up, so shorter runs (three rounds
  of five claims rather than four) should keep more messages in the cheaper
  tier. Not yet measured.
- **Doc edits cost re-extraction.** 390 sections were extracted for a
  207-section bundle: 183 extractions (47%) redid sections whose key moved
  because a doc they follow was edited, and each re-extraction dropped
  answers (214, 54 and 77 in the three passes) that writers then answered
  again, about 345 × $0.0081 = $2.80.
- **Context in every session:** the briefing (1,844 characters) and the
  four knowledge rules APM installs (11,597 characters): about 3,400 tokens.
  The `write-docs` skill adds 3,618 characters (about 900 tokens) when an
  agent uses it; the other skills are 1,170 to 2,816 characters each. On
  Claude Opus 5.5 ($5 5-minute cache write, $0.20 cache read per million),
  the 3,400 tokens cost about $0.017 on the first turn and $0.0007 a turn
  after, about $0.05 over a 50-turn session.

Not counted:

- the session that dispatches the agents and reads their one-line
  summaries;
- the optional decision model (`kmctl audit judge`), billed by its own
  provider;
- the tokens an agent spends writing a doc itself. That is the agent's own
  work, not something kmctl adds, and no doc-writing session was measured.

One session on one repository; the per-unit figures depend on how long the
sections and the code a claim names are.
