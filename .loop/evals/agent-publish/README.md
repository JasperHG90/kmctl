---
type: eval
title: 'Eval: agent-publish'
description: 'Definition of done for agent-publish: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T07:44:41+00:00'
slug: agent-publish
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: 5ae28a63c22ef8a6b713c712b41f57e96bebcd1265e4ffff917ca2e5dd8bfe56
  at: '2026-10-17T07:44:41+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: publish with a report whose findings are all below --min-severity (default high) closes the open issue titled --title with a comment saying so, posts nothing when none is open, and exits 0.
  Fails when: an issue is created or edited, an open issue is left open or closed without a comment, or the exit code is not 0
- r2: publish with a finding at or above --min-severity creates the issue titled --title when none is open; when one is open it replaces the body and adds a comment that mentions the owners and gives the counts; the body holds the rendered report and, when GITHUB_RUN_ID is set, a link to the run.
  Fails when: no issue is created, a second one is created instead of editing the open one, the update adds no comment or the comment lacks the mentions, or the body lacks a finding or the run link
- r3: The issue body @-mentions the owners of the last * rule in CODEOWNERS, found in .github/, the root or docs/ in GitHub's order; --mention (repeatable) replaces them; with neither, it mentions no one.
  Fails when: owners from another rule or file are mentioned, --mention does not replace them, or a mention line appears with no owners
- r4: publish exits 1 when gh fails and writes no issue, and exits 2 with a message for a missing or invalid report.json.
  Fails when: a gh failure exits 0, or a bad report is posted or crashes with a traceback
- r5: action/knowledge-audit-issue.sh is gone. .github/workflows/knowledge-audit.yml has an audit job (no issues: write, no token) that runs the agent and uploads agent-report, and a publish job (needs: audit, issues: write) that downloads it and runs agent.py publish with GH_TOKEN. action.yml's audit mode runs the agent and uploads the artifact with no token; its publish mode downloads the artifact and runs publish with min_severity, mention and issue_title. Every astral-sh/setup-uv step in the workflow and in action.yml sets enable-cache: false, and no actions/cache step is used, so nothing the agent wrote reaches the publish job but the artifact.
  Fails when: the shell script remains, a job or mode that runs the agent can see a token or has issues: write, publish runs in the agent's job, or an input is missing or not passed, or a setup-uv step leaves its cache on or an actions/cache step appears
- r6: ADR 0017 gets a correction (separate job, GitHub-hosted runners only), and the how-to and architecture overview describe publish, the two jobs, its threshold, closing and the mentions; the bundle and docs check clean.
  Fails when: a page still names knowledge-audit-issue.sh or kmctl check fails
- r7: All of the repository's gates pass.
  Fails when: just lint or just test fails
- r8 (judgment): publish --help names every option, what it takes and its default.
  Fails when: an option lacks a description or its default
