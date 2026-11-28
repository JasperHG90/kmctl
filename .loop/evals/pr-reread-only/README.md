---
type: eval
title: 'Eval: pr-reread-only'
description: 'Definition of done for pr-reread-only: 20 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-27T10:49:18+00:00'
slug: pr-reread-only
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: 1cef5f73e6676e7a5017baf502422e9cf60e1fe5a2b3925c7defc051cfddaf72
  at: '2026-11-27T10:49:18+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: the scope takes a docs page, an architecture page, a stable decision and a draft decision whose sources the change touched, each with its status and changed files
  Fails when: any of the four is missing from the scope, or its status or files are wrong
- r2: the scope leaves out a superseded or deprecated decision, a handoff, the log, index pages and URL sources
  Fails when: any of them appears in the scope
- r3: a folder source matches a changed file under it as a prefix
  Fails when: a page whose folder source holds a changed file is missing
- r4: a run with nothing in scope writes a report saying no page names a changed file, exits 0, and never calls the model
  Fails when: the model is called, the exit is not 0, or no report is written
- r5: run takes only --model, --base-url, --api-key-env, --base (required), --repo, --out, --timeout and --max-requests
  Fails when: run accepts another option, such as --audit, --prompt, --skills, --context or --no-shell, or runs without --base
- r6: publish posts only a pull request comment: --pr is required and the issue options are gone
  Fails when: publish runs without --pr, or accepts --mention or --repo
- r7: the agent's tools are read_file, search_files and list_files only
  Fails when: any other tool, such as run_shell, is given to the agent
- r8: the shipped prompt names kmctl new decision --draft, kmctl verify with --by human:, and kmctl summary ack
  Fails when: the prompt lacks any of the three
- r9: the agent script carries no OpenTelemetry dependency or Langfuse code
  Fails when: the script header lists an opentelemetry package or the script names LANGFUSE
- r10: audit mode runs on a same-repository pull_request, skips a fork or Dependabot pull request with exit 0, and refuses schedule and workflow_dispatch
  Fails when: another outcome for any of those events
- r11: the action's inputs audit, prompt, prompt_file, system_prompt_file, context, skills and mention are gone
  Fails when: action.yml still declares any of them
- r12: the agent step passes --base origin/$GITHUB_BASE_REF and adds no base-branch worktree
  Fails when: the step lacks --base, or runs git worktree add, or passes --instructions-root
- r13: the publish step passes --pr with the pull request's number
  Fails when: the publish command lacks --pr
- r14: this repository's knowledge-audit workflow runs on pull_request only, both jobs carry the same-repository condition, only publish has pull-requests: write, and no Langfuse secret is passed
  Fails when: another trigger, a job without the condition, write access on the audit job, or a LANGFUSE variable
- r15: no doc, record or shipped file names a removed audit or option outside Corrections, superseded text, release notes, prototypes and the hermes workflows; tests may name them to assert they are gone
  Fails when: grep finds a removed name in a live file
- r16: the draft ADR 0060 exists as a draft and ADR 0005, 0017 and 0057 each end with a Correction that links it
  Fails when: 0060 is missing or not a draft, or one of the three lacks a Correction linking 0060
- r17: the repository's hooks pass on every file
  Fails when: prek run --all-files exits nonzero
- r18: run refuses a checkout whose git config holds a token header, since read_file can reach .git/config
  Fails when: run starts the agent with an http extraheader in git config
- r19: the arguments action.yml's run and publish steps build, captured from a stub uv, parse with the real agent.py parser
  Fails when: either step passes a flag or value agent.parser() rejects
- r20: the agent and publish commands this repository's knowledge-audit workflow runs parse with the real agent.py parser, and its audit job checks out with persist-credentials: false
  Fails when: a command fails to parse, or the checkout keeps credentials
