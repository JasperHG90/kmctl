---
type: plan
title: 'Plan: okf-summary-holistic'
description: The bundle's summary distils what the knowledge says and keeps a whole view of the project, rather than listing the decisions, which the indexes do.
tags:
- plan
slug: okf-summary-holistic
epic: null
depends_on: [okf-summary]
priority: 1
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:45:52+00:00'
---

# okf-summary-holistic

Relayed from: none

## Intent

The operator (2026-10-18, ask j-20261018T214524+0000-dc23e505): "Summary
should not list decisions verbatim, that's what index is for. Summary should
**summarize the knowledge in them** and **keep a holistic view of the repo**".

Measured: this repository's `.okf/summary.md` (v0.8.0) puts 6 of its 9
bullets and 17 of its 20 links in its Decisions section, one bullet per
group of ADRs, much as `.okf/decisions/index.md` lists them; the sections
`init` writes (`SUMMARY_SECTIONS` in `src/kmctl/kinds.py`: Decisions,
Architecture, Open work, Practices, Known gaps, with prompts in
`SUMMARY_PROMPTS` in `src/kmctl/scaffold.py` such as "linking each
decision") are sorted by concept folder, so they steer every new summary to
the same shape.

What changes:

- **Sections by what a reader needs, not by folder.** The summary's
  sections become: **The project** (what it is for and who uses it, in a few
  sentences), **How it works** (the design as a whole: the parts and how they
  fit, the main flows), **What it has settled** (the knowledge the decisions
  and practices hold, distilled into the principles and constraints a
  newcomer must work within, with the reasons, each citing its sources
  inline, never one bullet per decision), and **Where it stands** (what
  works, what is open or in flight, and the known gaps). `SUMMARY_SECTIONS`,
  `SUMMARY_PROMPTS` and `SUMMARY_LINE` change; `kmctl schema summary` follows.
- **The guidance says so.** The skeleton's prompts, the AGENTS.md block's
  duty, the okf-bundle rule (`apm/claude/.apm/instructions/okf-bundle.instructions.md`,
  its Antigravity copy and `.claude/rules/okf-bundle.md`) and
  `docs/reference/commands.md` say: summarise what the knowledge says as a
  whole and link the concepts as evidence; the indexes list them.
- **This repository's summary is rewritten** in the new sections, at most
  500 words, synthesising the bundle rather than listing it.
- **The record.** ADR 0027 gains a Correction naming the new sections and
  why (`kmctl decision supersede` is for a reversed choice; this one keeps
  the summary and changes its shape).

Done when: `kmctl init` writes the four new sections with their prompts,
`kmctl schema summary` lists them, the guidance in the rule and the block
says to synthesise rather than list, and this repository's summary uses the
four sections, holds no section that is a list of one item per decision, and
passes `kmctl check`.

Out of scope: a check that a summary does not list decisions; whether a
page synthesises is judged by the reviewer and the reader, not counted.

## Could invalidate this plan

- none
