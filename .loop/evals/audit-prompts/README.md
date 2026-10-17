---
type: eval
title: 'Eval: audit-prompts'
description: 'Definition of done for audit-prompts: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:39:53+00:00'
slug: audit-prompts
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: e1a98dab5702497cf7ea3067e64e4954340fe0659463b34a9fc13b34acc98d90
  at: '2026-10-17T17:39:53+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: action/prompts/ holds docs-vs-code.md, okf-vs-code.md and okf-vs-docs.md, and run --audit NAME sends that file's text as the user message for each of the three names.
  Fails when: a prompt file is missing or empty, or --audit NAME sends anything but that file's text
- r2: run with no --audit, --prompt or --prompt-file sends okf-vs-code.md; --audit with --prompt or --prompt-file exits 2 naming both; an unknown --audit name exits 2; --help lists the three names.
  Fails when: the default is anything but okf-vs-code.md, a combination is accepted, an unknown name runs, or --help leaves out a name
- r3: action.yml's audit mode passes its audit input to --audit, and both its audit and publish modes use the report_name input (default agent-report) as the artifact name; .github/workflows/knowledge-audit.yml runs the audit and publish jobs as a matrix over docs-vs-code, okf-vs-code and okf-vs-docs with fail-fast off, each uploading and downloading its own agent-report-NAME artifact and publishing to its own issue title, publish running unless the run was cancelled, with the audit job still holding no token and no cache.
  Fails when: an audit is missing from either matrix, two audits share an artifact or an issue title, the action ignores report_name in either mode, one failed audit stops the other publishes, or the audit job gains a token or cache
- r4 (judgment): The how-to's section 5 names the three audits and the audit input, the tutorial points at --audit, ADR 0017 has a correction for the shipped audits, and the architecture overview shows the prompts.
  Fails when: a reader would still think the default audit checks only the .okf/ concepts that are due, or could not find how to pick an audit
