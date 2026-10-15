---
type: eval
title: 'Eval: audit-agent-and-skills'
description: 'Definition of done for audit-agent-and-skills: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev77+gbd4712cf8.d20261015
  at: '2026-10-15T12:28:25+00:00'
slug: audit-agent-and-skills
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: f7e8da8ed1bd79203050e24bfffb33b5b26c397bad0869d02d7e977977b3aec4
  at: '2026-10-15T12:28:25+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The kmctl-auditor agent's tools are exactly Read, Grep and Glob, so the audit cannot write (I2).
  Fails when: plugin/agents/kmctl-auditor.md lists any tool other than Read, Grep and Glob, or lists no tools (which would inherit all)
- r2: A findings sample the agent produced in a real run matches the defined shape.
  Fails when: plugin/skills/audit/evals/sample-findings.json is not a JSON list of objects with concept, path, review (architecture|decision|practice), verdict (holds|drifted|unsure), summary and evidence (list of path:line strings)
- r3: The audit skill gets the due list from kmctl review due --json, keeps only architecture, decision and practice concepts, batches them, and hands them to kmctl-auditor.
  Fails when: plugin/skills/audit/SKILL.md does not name kmctl review due --json, the three in-scope sections, batching, and the kmctl-auditor agent
- r4: The three review skills exist and the agent follows them.
  Fails when: any of plugin/skills/architecture-review, decision-log-review or practices-review has no SKILL.md, or the agent's prompt does not name all three
- r5 (judgment): The skills and agent were made with skill-creator, tried on this repository and on loop-harness at /home/vscode/workspace, and results.md counts real and false drift from the loop-harness run.
  Fails when: no test prompts or results are kept beside the audit skill, the loop-harness run is missing, or real and false drift are not counted
