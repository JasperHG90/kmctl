---
type: eval
title: 'Eval: init-seeds-the-habit'
description: 'Definition of done for init-seeds-the-habit: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:03:35+00:00'
slug: init-seeds-the-habit
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: d82018173c96f03e0ccd3deca9ef86fd0ec815e5d0dc39d18bec04d27a11203e
  at: '2026-10-15T16:03:35+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init writes the four knowledge rules to .claude/rules/ in full with their paths: front matter, written for any repository, and keeps an existing file of the same name.
  Fails when: after init in an empty repo any of okf-bundle, docs-layout, diagrams-stay-current or manifesto-invariants is missing from .claude/rules/, lacks its paths: front matter or a WHY paragraph, or mentions loopctl, tickets or .loop/; or an existing file of that name is changed
- r2: kmctl init writes CLAUDE.md with a kmctl block (routing table and three duties) when there is none, appends the block to an existing CLAUDE.md, and replaces only the block when it is already there.
  Fails when: the block between <!-- kmctl:start --> and <!-- kmctl:end --> is missing the routing for docs/, the manifesto, decisions/ and architecture/ or any of the three duties; an existing CLAUDE.md loses or changes any text outside the block; or a second init adds a second block
- r3: kmctl init records decision 0001, Keep project knowledge in an OKF bundle, with Context, Decision naming the rejected alternatives, and Consequences, plus its index entry and log line; kmctl check and the strict okf validator pass right after init.
  Fails when: after init the decision is missing, lacks any of those sections or the rejected alternatives, has no index entry or log line, or kmctl check or okf_validate --strict fails
- r4: kmctl init prints the agent's next steps in order: fill the manifesto's purpose and invariants (values are the operator's), add an architecture page once there is code, record each choice with kmctl new decision.
  Fails when: init's output lacks any of the three steps or gives them in another order
- r5: Running kmctl init twice changes nothing the second time.
  Fails when: a second init in the same repo changes, adds or removes any file
- r6: The other init, briefing and check tests still pass, and the briefing stays within its word budget.
  Fails when: any test in tests/test_init.py, tests/test_briefing.py or tests/test_check.py fails
- r7 (judgment): A spike reruns spike 1's task with the built kmctl init and the real SessionStart briefing and counts decisions and architecture pages against spike 1's arms.
  Fails when: no init-seeds-the-habit spike after the build records both counts for the built init
