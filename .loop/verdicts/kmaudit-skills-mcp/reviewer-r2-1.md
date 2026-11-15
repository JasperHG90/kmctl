---
type: verdict
title: 'Verdict: kmaudit-skills-mcp reviewer round 2'
description: 'reviewer verdict for round 2 of kmaudit-skills-mcp: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T09:44:16+00:00'
slug: kmaudit-skills-mcp
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Narrow round. f2 is fixed in both results.md files. f1 is half fixed. The
extract-claims run shows the main session sending the work to
kmaudit-claims-extractor, and the agent storing claims through
`claims_submit` with no shell. That was the real risk. write-checks has not
had the same run. The new SKILL.md sentence is accurate and does no harm.
Nothing blocks.

## Checked

- Gates: I reran `loopctl gate stamp` in the worktree. Lint, format, tests
  and integration pass, eval rows r1 to r5 pass, "stamp green:
  74d5c007b1ad27a45155c30ef5cd8d67f8452f7703abbc915a910f88aaafbc37".
- Transcripts: I parsed transcript.jsonl, transcript2.jsonl and
  transcript3.jsonl myself. In all three the kmaudit project server is
  connected and kmaudit-claims-extractor is loaded. Run 3: the main session
  calls ToolSearch, then `claims_todo` on `<repo>/.okf`, then dispatches the
  agent once. The agent calls `claims_todo` per concept and
  `claims_submit` twice, with `by: kmaudit-claims-extractor` and the
  namespace folder. Nobody calls Bash. The final reply shows counts only:
  0 pending, 3 point claims and 1 subjective. Run 2 has the one main-session
  Bash `ls -d .okf docs` that results.md describes. These match what
  results.md claims.
- The SKILL.md sentence (no folder named: call the todo tool on the root's
  `.okf` straight away, and its refusal says when the folder is missing): I
  called `claims_todo` and `checks_todo` from mcp_server.py on a repo with
  no `.okf`. Both raise ToolError "... .okf does not exist; give a folder of
  markdown docs or a page in one". So the sentence is true. It also fits
  step 1's "a tool error is a refusal: quote it and stop". In write-checks
  it is the same sentence with `checks_todo`, which is right.
- f2: both results.md files now credit
  `packages/kmaudit/tests/test_apm_package.py` with the agents' tools check
  and test_skills.py with the tool-name and no-shell checks.

## Findings

- f1 (open, missing, not blocking): extract-claims is covered end to end.
  results.md says "write-checks and the no-agent eval were not run", and
  write-checks' results.md still says its evals were not rerun. The
  check-writer uses the same mechanism (a subagent calling project MCP
  tools) that run 3 proved, so a plain rerun of run.sh's shape for
  /write-checks after the claims run is enough. I do not need to see it
  again. Results go in write-checks' results.md.
- f2 (resolved): fixed in both results.md files, as above.

## Notes

Run 2's `claims_submit` call had no `by` field. Run 3's calls do. The agent
file asks for it, so this is model variance, not a defect. The `.summary`
file for run 1 reads "1 1 1", but the transcript shows no Bash call. That
fits results.md's note that run 1's script output was wrong. It does not
affect run 3.
