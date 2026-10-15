---
type: plan
title: 'Plan: init-seeds-the-habit'
description: "kmctl init sets a repository up so an agent keeps its knowledge: it writes the knowledge rules as files, adds a kmctl block to CLAUDE.md, records the first decision (keep knowledge in OKF), and tells the agent what to write next."
slug: init-seeds-the-habit
epic: knowledge
depends_on: []
priority: 3
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T15:52:06+00:00'
---

# init-seeds-the-habit

Relayed from: operator, 2026-10-15, after an agent in a kmctl repository wrote code and left the bundle nearly empty: rules "should be included either as briefing or by CLI writing them using init"; "CLAUDE.md --> either append when doing init or write if it doesn't exist"; "Instruct the agent when initing to write manifesto, record architectural choices, and CLI init should write first decision to capture knowledge in .okf / use OKF".

## Intent

In this repository and in loop-harness, knowledge stays current because of things kmctl does not ship: 23 rule files loaded by path, a `CLAUDE.md` that routes to `.okf/`, a seeded bundle agents copy, and a reviewer whose consistency lens reads those rules. A fresh `kmctl init` writes four files and nothing else, so an agent gets a briefing and empty templates. `kmctl init` changes to seed the habit, never overwriting a file the repository already has:

- Rules as files: it writes the knowledge rules `okf-bundle`, `docs-layout`, `diagrams-stay-current` and `manifesto-invariants` to `.claude/rules/`, in full with their WHY paragraphs and `paths:` front matter, from package data. The packaged copies are written for any repository: no mention of loopctl, tickets or this repository's own files. The briefing keeps its one-line form of the same rules, so other harnesses still get them (ADR 0002). An existing rule file of the same name is kept and reported.
- `CLAUDE.md`: it adds a block between `<!-- kmctl:start -->` and `<!-- kmctl:end -->` holding the routing table (what goes in `docs/`, the manifesto, `decisions/`, `architecture/` and the rest) and three duties: record each choice as a decision when it is made, keep `architecture/` matching the code, and run `kmctl check` before finishing. With no `CLAUDE.md` it writes the file with that block; with one it appends the block; with the block already there it replaces only the block.
- First decision: it records decision 0001, "Keep project knowledge in an OKF bundle", in the target repository's decisions folder through `kmctl new decision`'s writer, with real Context, Decision (the rejected alternatives: a wiki, README-only notes, nothing), and Consequences, plus its index entry and log line.
- Next steps: its output ends with what the agent does next, in order: fill the manifesto's purpose and invariants (values are the operator's), add an architecture page once there is code, and record each choice with `kmctl new decision`.

Measured on the operator's failing session: the agent made 6 design choices and recorded 1, wrote 0 architecture pages, and left the manifesto's values empty; a fresh `kmctl init` today writes 0 rule files, 0 lines of `CLAUDE.md` and 0 decisions.

Done when tests show init writes the four rule files with their front matter and keeps an existing one; writes, appends to, or replaces only its block in `CLAUDE.md`; writes decision 0001 with all four sections, its index entry and log line, and `kmctl check` and the strict okf validator pass right after init; prints the next steps; and running init twice changes nothing the second time. A spike reruns spike 1's task with the built `kmctl init` and the real SessionStart briefing, and counts decisions recorded and architecture pages written against spike 1's arms.

## Could invalidate this plan

- Settled for this setup by spike:init-seeds-the-habit/1: on one FastAPI task with three runs per arm, seeding raised architecture pages from 0 of 3 runs to 3 of 3 and decisions from a mean of 3.0 to 4.3, with `kmctl check` passing in all six. The unseeded arm did not reproduce the operator's 1-of-6 failure, likely because the briefing went in the prompt text there, so the decision gain is the smaller result.
