---
type: eval
title: 'Eval: adr-0057-pr-audit'
description: 'Definition of done for adr-0057-pr-audit: 13 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T13:02:14+00:00'
slug: adr-0057-pr-audit
signoff:
  signer: delegated:jasperginn@gmail.com/implement-ticket
  hash: 7d982070eb81aa82eaf0b3784c1c00790022dbf3424bb1301268a31e31ecc4dc
  at: '2026-11-26T13:02:14+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The Context links ADR 0055
  Fails when: the record has no link to 0055-one-verify-for-the-pages-a-branch-made-due
- r2: The Context says kmctl review due --base compares sources only for verified decisions, with the measured 0 of 86 over 15 pull requests
  Fails when: the record does not name review due --base, or does not give the 86 figure
- r3: The scoping rule still matches a decision's sources against the changed files, a folder source as a prefix
  Fails when: the scoping rule drops its own sources matcher or says nothing of folder sources
- r4 (judgment): The record says what the audit adds over ADR 0055: whether a decision still holds, not only which pages a change touched
  Fails when: a reviewer finds no sentence that tells the audit's judgment apart from 0055's list
- r5: A fork pull request is skipped with a notice and exit 0, so it gets no red check
  Fails when: the fork rule still says the action refuses the fork pull request, or never says it exits 0
- r6 (judgment): The instructions rule says the base-branch checkout keeps a pull request from loosening the audit that checks it, and does not guard the key, since the pull request's own workflow file runs
  Fails when: a reviewer finds the base-branch checkout still presented as protecting the API key, or no mention that a pull_request run uses the pull request's workflow file
- r7: The new shipped audit has one name, used the same way throughout and next to the three in AUDITS
  Fails when: the record calls it 'fourth' in one place and 'new' in another, or never names it
- r7b (judgment): Reviewer confirms the audit's name is used consistently and fits AUDITS in action/agent.py
  Fails when: a reviewer finds the audit unnamed or named two ways
- r8: The record says the merge-base comparison relies on the audit's existing fetch-depth: 0 requirement
  Fails when: the record does not mention fetch-depth: 0
- r9: The record places the feature under ADR 0046's split between kmctl and kmaudit
  Fails when: the record has no link to ADR 0046
- r10: The record stays a draft for the operator to accept
  Fails when: the front matter status is not draft
- r11: The repo's pre-commit hooks pass on every file, including strict OKF validation of .okf/
  Fails when: prek run --all-files exits nonzero
- r12: The ticket's branch carries PR 71's head, so pushing it to adr/audit-pull-requests is a fast-forward
  Fails when: origin/adr/audit-pull-requests is not an ancestor of HEAD
