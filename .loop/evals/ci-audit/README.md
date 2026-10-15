---
type: eval
title: 'Eval: ci-audit'
description: 'Definition of done for ci-audit: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:45:11+00:00'
slug: ci-audit
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: ba43b3226ba2dda61656c71564e6c17f1f44f7dad4669401b1161fb2b6cca9c6
  at: '2026-10-15T12:45:11+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: action.yml has an optional mode input (checks by default, or audit) and an anthropic_api_key input; without mode the action runs only the checks, as before.
  Fails when: action.yml has no mode input, its default is not checks, the audit step runs when mode is not audit, or the existing checks tests fail
- r2: The audit path runs kmctl review due --json itself, hands the due list to claude -p, and writes the agent's findings to the job summary and to one issue titled Knowledge audit.
  Fails when: with a stub claude that prints a findings block and a stub gh, the summary or the issue body does not hold each finding's concept and verdict, or gh is not asked to create or edit an issue titled Knowledge audit
- r3: Audit mode refuses any event other than workflow_dispatch and schedule, before claude runs.
  Fails when: with GITHUB_EVENT_NAME=pull_request (or push) the script exits 0, or the stub claude is called
- r4: claude runs with the action's own plugin and read-only tools: --plugin-dir pointing at the action's plugin/, --allowedTools Read,Grep,Glob and --disallowedTools Bash,Edit,Write.
  Fails when: the stub claude's recorded arguments lack any of those flags or values
- r5: A findings block that is missing or not valid JSON fails the step with a message, and opens no issue.
  Fails when: with a stub claude that prints no findings block, the script exits 0 or gh is called
- r6: The shipped example audit workflow runs only on workflow_dispatch and schedule, sets permissions contents: read and issues: write, and passes the key from a secret.
  Fails when: .github/workflows/knowledge-audit.yml has another trigger, other permissions, or no secrets reference for the key
- r7 (judgment): A spike shows that real claude -p with these flags and --plugin-dir loads the plugin and refuses a request to run Bash or to write a file.
  Fails when: no spike for ci-audit records the flags, the plugin load, and both refusals
