---
type: verdict
title: 'Verdict: ci-audit reviewer round 1'
description: 'reviewer verdict for round 1 of ci-audit: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:09:26+00:00'
slug: ci-audit
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The read-only flag set, the event guard, the example workflow and the report parser are right, and every gate is green. Two defects in the audit path block the commit. First, the prompt depends on a skill the session cannot load (f1). Second, a run with nothing in scope due fails the job (f2). The stubbed tests cannot catch either one. Two small hardening points are also included (f3, f4).

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests and rows r1 to r6 pass, "stamp green: 86047631e7d55abe54e87ce5949097e961a71c61981624a90e8b495f6dec8aaa".
- I read the staged diff and every changed file in full: action.yml, action/knowledge-audit.sh, action/audit-report.py, .github/workflows/knowledge-audit.yml and tests/test_ci_audit.py. Note that `git diff main...` also shows .loop files, but those come from main moving on.
- Rows r1 to r6: each test asserts its row's fails_when. r1 checks the default and the `if:` guards on the steps. r2 checks concept and verdict in both the summary and the body, plus an `issue create` titled Knowledge audit. r3 covers pull_request, push, pull_request_target and an unset event, and checks that claude was never called. r4 checks each flag value and that the prompt goes on stdin. r5 covers no block, bad JSON and the wrong shape, and checks that gh is never called. r6 checks the triggers, the permissions and the secret.
- r7 (judgment): passes. Spike 3 records the flag set (without --strict-mcp-config, and with stream-json). Its init tools were only Task, Glob, Grep and Read, kmctl:kmctl-auditor was among the init agents and dispatched, and the notebook stayed unchanged. Spike 2 records that the plugin loaded as kmctl@inline. --strict-mcp-config only drops MCP servers. The real `claude --help` (2.1.300, the pinned version) lists it, and also --tools, --allowedTools, --disallowedTools, --setting-sources and --plugin-dir, all spelled as the script uses them. The help also says `--output-format json` prints a single result object, and that is what audit-report.py reads (`.result`). I judge both untested flags low risk.
- gh lookup: `--search '"Knowledge audit" in:title'` followed by an exact title match in python is correct. `gh issue list` returns issues only.
- Writes: none of the four write tools is offered, and the subagents inherit --disallowedTools (spike 2). The plugin's SessionStart hook runs `kmctl briefing`, which is read-only. I found no file writes in briefing.py.
- Consistency: there is no docs/ folder. The action.yml description and the workflow comment state the permissions note, and they agree with I2 and ADR 0005.

## Findings

- f1: skills/audit/SKILL.md reaches the model only through the Skill tool, and --tools leaves that tool out. Spike 2's session called `Skill kmctl:architecture-review`, and that is how it got the review text. Spike 3 found that Skill is not needed when the prompt carries the instructions, but this prompt does not carry them. Fix: tell the model to Read `${KMCTL_PLUGIN_DIR}/skills/audit/SKILL.md` by its exact path (and the review skills next to it), or put the steps in the prompt. Then run the real script once in a spike, against a fixture with an architecture or decision page that is due.
- f2: filter the due list in the script, keeping architecture/, decisions/ and practices/. When nothing is left, write "nothing in scope is due" to the summary, exit 0 and skip claude. Or have the prompt require a `[]` block. Add a test for this case. Also point the r2 fixture at a concept the audit actually covers.
- f3: hardening, not blocking.
- f4: hardening, not blocking. Use `set -o pipefail` or check gh's exit status before you create an issue.

## Notes

`--setting-sources project` loads the audited repository's own .claude/settings.json hooks, and those run shell commands outside the tool limits. That code belongs to the repository and runs from the default branch, so I did not file it. The audit agent itself cannot trigger a write through it.
