---
type: eval
title: 'Eval: agent-publish'
description: 'Definition of done for agent-publish: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T07:40:49+00:00'
slug: agent-publish
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: c4c9fc8bc129508b596321712198f079355826b6eeeaa159a947a01667898555
  at: '2026-10-17T07:40:49+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: publish with a report whose findings are all below --min-severity (default high) calls gh for nothing, exits 0 and says no issue was written.
  Fails when: gh is called to list, create or edit an issue, or the exit code is not 0
- r2: publish with a finding at or above --min-severity creates the issue titled --title when none is open, and edits the open one when it is; the body holds the rendered report and, when GITHUB_RUN_ID is set, a link to the run.
  Fails when: no issue is created, a second one is created instead of editing the open one, or the body lacks a finding or the run link
- r3: The issue body @-mentions the owners of the last * rule in CODEOWNERS, found in .github/, the root or docs/ in GitHub's order; --mention (repeatable) replaces them; with neither, it mentions no one.
  Fails when: owners from another rule or file are mentioned, --mention does not replace them, or a mention line appears with no owners
- r4: publish exits 1 when gh fails and writes no issue, and exits 2 with a message for a missing or invalid report.json.
  Fails when: a gh failure exits 0, or a bad report is posted or crashes with a traceback
- r5: action/knowledge-audit-issue.sh is gone; action.yml's audit mode and .github/workflows/knowledge-audit.yml run agent.py publish on report.json in the only step that gets GH_TOKEN, and action.yml has min_severity, mention and issue_title inputs passed to it.
  Fails when: the shell script remains, the issue step does not run publish, another step gets the token, or an input is missing or not passed
- r6: ADR 0017 gets a correction, and the how-to and architecture overview describe publish, its threshold and the mentions; the bundle and docs check clean.
  Fails when: a page still names knowledge-audit-issue.sh or kmctl check fails
- r7: All of the repository's gates pass.
  Fails when: just lint or just test fails
- r8 (judgment): publish --help names every option, what it takes and its default.
  Fails when: an option lacks a description or its default
