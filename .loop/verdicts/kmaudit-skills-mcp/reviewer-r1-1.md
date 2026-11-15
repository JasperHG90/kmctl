---
type: verdict
title: 'Verdict: kmaudit-skills-mcp reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-skills-mcp: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T09:31:34+00:00'
slug: kmaudit-skills-mcp
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The move is done as the plan says. kmaudit's package holds the two skills
and declares the kmaudit server from its own tag. The Claude-only
sub-package holds the two renamed agents with Read, Grep, Glob and their
MCP tools, and no Bash or hook. kmctl's package, wheel and translations no
longer carry them. `set --package kmaudit` pins the server ref and the
sub-package version, and refuses when either is missing. Docs, okf pages
and the ADR amendment agree with the code. Nothing blocks. The one real gap
is f1: no run shows the agents working through MCP. An operator should run
the evals in a session with the kmaudit server before this ships to users.

## Checked

- Gates: `loopctl gate stamp` rerun in the worktree, result quoted in Notes.
- r1: test_apm_package.py checks the skill set, the `./claude` dependency,
  `targets == ["claude"]`, the exact uvx args at `kmaudit-v{base_version}`,
  the exact tools list per agent, and no `hooks` or Bash. It also checks the
  five tools exist on the server. Breaking any of these fails a test.
- r2: kmctl tests assert the agents folder holds only kmctl-auditor, the
  skills list drops the two, the wheel has no kmaudit skill or agent file,
  and the plugin patch writes only bundle-weaver, event-analyzer and
  kmctl-auditor for both harnesses. The auditor and the audit skill stay
  asserted.
- r3: test_release.py covers set moving the server ref (0.1.0 to 0.2.0 to
  0.3.0), the line-level diff of the manifest, and the refusals for a
  missing server and a missing or versionless claude apm.yml, with nothing
  written. The `_KMAUDIT_INSTALL` regex does not match the `{git: ...}`
  comment in apm.yml, so only the server line moves.
- r4: I ran the integration test myself: 1 passed. It installs from a
  file:// rewrite of a tagged copy and checks .mcp.json, opencode.json,
  byte-equal agents in .claude/agents/, none in .opencode/agents/, and the
  skills for both harnesses.
- r5: test_skills.py checks no `kmaudit <group>` command in code spans
  (the group list matches every top-level CLI command), every named
  `claims_*`/`checks_*` tool exists on the server, the no-agent step, and
  that agents submit to the namespace folder with `by` set to their name.
  The "evals pass" half of the row has no command (f1).
- Read the skills and agents against mcp_server.py: `folder`, `answers`,
  `by`, `brief` and the `concepts`/`path`/`sections`/`claims` fields they
  name exist. release.yml stages the claude apm.yml. kmctl's opencode.py
  "three agents" docstring is now correct.
- The kmctl briefing no longer listing /extract-claims and /write-checks is
  right: those skills are no longer kmctl's, the harness lists installed
  skills itself, and kmaudit's own briefing still points at them.
- Remaining `kmctl-claims-extractor` mentions are in ADR prose (kept on
  purpose), log history, prototypes and negative test assertions.

## Findings

- f1 (missing, not blocking): the evals were not rerun. The reason given
  holds (the loop refuses a nested claude session), and the plan's spike
  already showed a subagent can call a project MCP tool. But nothing shows
  these agents and skills working end to end. The fix is to run the evals,
  not to change code, so I do not need to see it again. The operator should
  run it before release.
- f2 (docs, not blocking): results.md credits test_skills.py with the
  agents' tools check. Name test_apm_package.py for it.

## Notes

`loopctl gate stamp` in the worktree: lint, format, tests and integration
pass; eval rows r1 to r5 pass; "stamp green:
2be1566cbfc5da5665f2042e5657945765ce41255f15bb1b38da20ad79dc716a".
