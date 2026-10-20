---
type: eval
title: 'Eval: hermes-workflows'
description: 'Definition of done for hermes-workflows: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev82+g0ed6ce5f1.d20261019
  at: '2026-10-20T08:32:13+00:00'
slug: hermes-workflows
signoff:
  signer: delegated:jasperginn@gmail.com/planner
  hash: f1fe5224e237fce1a27509f347c66141fab3a4e6534fb6cc97d6d1c79d02b6bb
  at: '2026-10-20T08:32:13+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Both Hermes workflows start on /hermes or /triage from a member, and no workflow or prompt says @hermes
  Fails when: hermes-interactive.yaml's trigger_phrase or job condition is not /hermes, either job runs for a comment from someone outside MEMBER, OWNER or COLLABORATOR, or '@hermes' appears in either workflow or prompt
- r2: hermes-interactive.yaml reads its prompt and skills from the default branch, never from the pull request
  Fails when: system_prompt_file or skills_dir points outside the checkout of the default branch
- r3: Every action in both Hermes workflows is pinned by commit SHA
  Fails when: a uses: line in either workflow names a tag or branch instead of a 40-character SHA with its version comment
- r4: scripts/hermes_triage.py cuts a triage comment longer than 800 characters (about 200 tokens) at a line break and keeps it at most 800 characters
  Fails when: a 2000-character response is posted longer than 800 characters, or is cut in the middle of a line
- r5: scripts/hermes_triage.py applies only allowed labels and the priority label from the trailer, and strips the trailer from the comment
  Fails when: a label outside the type, area/* or priority/* lists is applied, the priority label is missing, or the trailer appears in the posted comment
- r6: The triage system prompt asks for a comment under 200 tokens, and the workflow's area labels match kmctl's top-level layout
  Fails when: issue-triage-system.md does not state the 200-token limit, or TRIAGE_AREAS names a folder kmctl does not have
- r7 (judgment): An ADR records why kmctl's repository runs Hermes for /hermes and triage beside action/agent.py, which ADR 0017 chose for the audit
  Fails when: no accepted ADR covers the Hermes workflows, or it contradicts ADR 0017's audit decision
