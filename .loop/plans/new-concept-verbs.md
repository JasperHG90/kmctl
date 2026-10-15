---
type: plan
title: 'Plan: new-concept-verbs'
description: "kmctl new creates a decision, practice, proposal, prototype or handoff with its front matter, number and index entry."
slug: new-concept-verbs
epic: cli
depends_on: [scaffold-init, knowledge-check]
priority: 5
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:20+00:00'
---

# new-concept-verbs

Relayed from: none

## Intent

`kmctl new decision|practice|proposal|prototype|handoff TITLE --description TEXT` writes one concept and indexes it in the format knowledge-check defines:

- the file name is the title in kebab-case, with the next four-digit number in front for decisions; a prototype is a folder with `README.md`;
- front matter: `type`, `title`, the given `description`, `tags`, `generated` (by and at), and for handoffs a `stale_after` date;
- the body is a skeleton of that kind's section headings (for a decision: Context, Decision, Consequences), which the agent fills in afterwards;
- the first concept in a section creates the section folder, its `index.md`, and the section's link in the root index;
- the entry goes into the section index, and a dated line naming the concept id goes into `.okf/log.md`.

It refuses, writing nothing, when the file already exists. Updating an existing handoff (for a second `/handoff` in one session) is handoff-and-continue-skills's job.

Done when tests show each kind is created and indexed, the first concept of a section creates the section, `kmctl check` passes afterwards, the bundle passes the pinned okf validator in strict mode, and the refusal fires.

The okf validator in tests is a pinned, test-only copy of `okf_validate.py` from okf-skills 0.10.1 (MIT), kept with its licence under tests/vendor/ and run in strict mode with pyyaml as a dev dependency. The first ticket that needs it adds it.

## Could invalidate this plan

- none
