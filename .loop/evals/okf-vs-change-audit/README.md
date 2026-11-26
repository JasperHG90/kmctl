---
type: eval
title: 'Eval: okf-vs-change-audit'
description: 'Definition of done for okf-vs-change-audit: 26 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T13:37:20+00:00'
slug: okf-vs-change-audit
signoff:
  signer: delegated:jasperginn@gmail.com/create-eval
  hash: b88972c6c8197c2bdd80b9e0247dbc09842a25bddfcc31e7807299aa8398d73f
  at: '2026-11-26T13:37:20+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: okf-vs-change matches a stable decision whose file source the change touched
  Fails when: the decision is missing from the matched list
- r2: okf-vs-change matches a folder source as a prefix of a changed file
  Fails when: a decision whose folder source holds a changed file is missing
- r3: okf-vs-change leaves out draft decisions and URL sources
  Fails when: a draft decision or a URL source appears in the matched list
- r4: the matched decisions appear in the task the agent gets
  Fails when: the user message does not list the matched decisions
- r5: --audit okf-vs-change without --base exits 2 with a message naming --base
  Fails when: it exits other than 2 or the message does not name --base
- r6: okf-vs-change is in AUDITS and in run --help
  Fails when: AUDITS or --help lacks okf-vs-change
- r7: with --instructions-root DIR, a tracked relative --prompt-file, --system-prompt-file, --context and --skills resolve under DIR
  Fails when: any of them resolves against the current folder
- r8: with --instructions-root DIR, a --context folder git does not track stays in the working tree
  Fails when: the untracked folder is looked up under DIR or dropped
- r9: without --instructions-root, every path resolves as before
  Fails when: a path resolves differently without the flag
- r10: the action's event check lets workflow_dispatch, schedule and a same-repository pull_request run
  Fails when: any of them is refused
- r11: a fork pull_request, or one Dependabot opened, gets a notice, exit 0, and a step output that skips the agent step
  Fails when: the step exits nonzero, prints no notice, or sets no output that keeps the agent step from running
- r12: pull_request_target, push and other events stay refused
  Fails when: any of them is let through
- r13: the agent step passes --instructions-root and --base only on a pull_request event
  Fails when: they are passed on another event or missing on a pull request
- r14: publish --pr N creates one marked comment, and a second run edits that comment and posts no other
  Fails when: the second run posts a new comment or edits none
- r15: publish with no report posts nothing and exits 0, in issue and pull request mode
  Fails when: it exits nonzero or calls gh
- r16: the action's publish step passes --pr on a pull_request event
  Fails when: --pr is missing on a pull request or passed on another event
- r17: ADR 0005 and ADR 0017 each have a dated Correction linking ADR 0057
  Fails when: either record lacks a Correction section that links 0057
- r18: ADR 0057 stays a draft, says fetched context folders stay in the working tree, and no longer says nothing is built before acceptance
  Fails when: status is not draft, the fetched-context sentence is missing, or the old last Consequence remains
- r19: the knowledge-audit workflow no longer says the audit never runs on a pull request
  Fails when: the comment still says it never runs on a pull request
- r20: the how-to page shows a pull request workflow with the same-repository condition
  Fails when: the page has no head.repo.full_name condition
- r21 (judgment): the okf-vs-change prompt keeps the audit report-only and asks for a reason for each decision the agent adds beyond the matched list
  Fails when: a reviewer finds the prompt lets the agent edit files or add decisions without a reason
- r22: the repo's pre-commit hooks pass on every file
  Fails when: prek run --all-files exits nonzero
- r23: the ticket's branch carries PR 71's head, so the push is a fast-forward
  Fails when: origin/adr/audit-pull-requests is neither an ancestor of HEAD nor the merge in progress
- r24: the action's publish mode does not fail on a missing report artifact
  Fails when: a missing artifact fails the publish step
- r25: the knowledge-audit workflow's report download does not fail publish on a missing artifact
  Fails when: the download-artifact step in the publish job lacks continue-on-error: true
- r26: with --instructions-root DIR, an instruction path the pull request tracks but DIR does not have exits 2
  Fails when: it falls back to the working tree or exits other than 2
