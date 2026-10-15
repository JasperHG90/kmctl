---
type: eval
title: 'Eval: init-seeds-the-habit'
description: 'Definition of done for init-seeds-the-habit: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:06:19+00:00'
slug: init-seeds-the-habit
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 103ecd8140bbeec515500a526dd82a0d6e92f9953a9fd75e352e397c0a5e2d18
  at: '2026-10-15T16:06:19+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init writes the four knowledge rules to .claude/rules/ in full with their paths: front matter, written for any repository, and keeps an existing file of the same name.
  Fails when: after init in an empty repo any of okf-bundle, docs-layout, diagrams-stay-current or manifesto-invariants is missing from .claude/rules/, lacks its paths: front matter or a WHY paragraph, or mentions loopctl, tickets or .loop/; or an existing file of that name is changed
- r2: kmctl init adds a kmctl block (routing table and three duties) to each of CLAUDE.md and AGENTS.md that exists, once per real file, writes CLAUDE.md with the block when neither exists, and replaces only the block when it is already there.
  Fails when: the block between <!-- kmctl:start --> and <!-- kmctl:end --> is missing the routing for docs/, the manifesto, decisions/ and architecture/ or any of the three duties; an existing CLAUDE.md or AGENTS.md loses or changes any text outside the block; an existing AGENTS.md gets no block; a CLAUDE.md symlinked to AGENTS.md ends with two blocks; or a second init adds a second block
- r3: kmctl init records the decision Keep project knowledge in an OKF bundle, with Context, Decision naming the rejected alternatives, and Consequences, plus its index entry and log line, only when no record with that title exists; kmctl check and the strict okf validator pass right after init.
  Fails when: after init in a fresh repo the decision is missing, lacks any of those sections or the rejected alternatives, has no index entry or log line, or kmctl check or okf_validate --strict fails; or in a bundle that already has decisions 0001 to 0003, init writes a second record with that title or overwrites one
- r4: kmctl init prints the agent's next steps in order: fill the manifesto's purpose and invariants (values are the operator's), add an architecture page once there is code, record each choice with kmctl new decision.
  Fails when: init's output lacks any of the three steps or gives them in another order
- r5: Running kmctl init twice changes nothing the second time.
  Fails when: a second init in the same repo changes, adds or removes any file
- r6: The other init, briefing and check tests still pass, and the briefing's rules and word count are unchanged by the new rule files.
  Fails when: any test in tests/test_init.py, tests/test_briefing.py or tests/test_check.py fails, or kmctl briefing's text in a fresh repo after init differs from before apart from state counts
- r8: This repository records why init writes rule files and the agent-file block: a new decision record, a dated Correction on ADR 0002 pointing to it, and init's help and ScaffoldResult docstring naming the exception to never editing a kept file.
  Fails when: .okf/decisions/ has no record naming .claude/rules/ and CLAUDE.md that links ADR 0002 and ADR 0003, ADR 0002 has no Correction pointing to it, or kmctl init --help or ScaffoldResult's docstring still says init never edits a kept file without the exception
- r7 (judgment): A spike reruns spike 1's task with the built kmctl init and the real SessionStart briefing and counts decisions and architecture pages against spike 1's arms.
  Fails when: no init-seeds-the-habit spike after the build records both counts for the built init
