---
type: verdict
title: 'Verdict: okf-vs-change-audit plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of okf-vs-change-audit: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-26T13:36:11+00:00'
slug: okf-vs-change-audit
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Fail, round 1. The approach holds and the three listed risks are settled by
spikes. Two fact mismatches need a revision: P4/O4 fold two separate causes
and behaviours (p1), and O5 rewrites a workflow comment whose behaviour
nothing changes (p2).

## Checked

- Risk 1, delivery: spike adr-0057-pr-audit/2 shows the merge of PR 71 into a
  `loop/` worktree passes the backstop, pushes as a fast-forward, and that
  `ticket done` does not call `land`.
- Risk 2, PR comment permissions: spike okf-vs-change-audit/1 rests on
  GitHub's permission table, not a live run; the plan says so.
- Risk 3, base checkout: spike okf-vs-change-audit/2 copies checkout v7.0.1's
  fetch-depth 0 refspecs and shows `origin/<base>` is there, a detached
  worktree needs no token, and the three-dot diff lists exactly the PR's
  files, also when main moves.
- Code claims: `AUDITS` holds three audits; the event step refuses
  `pull_request` with exit 1; `publish` exits 2 on an unreadable report; the
  four instruction flags resolve against the current folder;
  `DEFAULT_SKILLS` and `PROMPTS` come from the action's checkout; agent.py
  already depends on PyYAML; the prototype's `matches()` (scope.py, staged in
  the adr-0057-pr-audit worktree) is the rule the plan describes.
- ADR 0057 (revised) already admits the PR's own workflow file can loosen
  the audit, so P3's limit is stated, not missed.
- 2.0 facts: needs, kinds and touches match the prose apart from p1 and p2.

## Findings

- p1: P4 and O4 each fold two separate things together; split them.
- p2: knowledge-audit.yml's own download step still fails on a missing
  artifact, so changing its comment alone makes the comment false.

## Notes

Left to the build, not findings: the "for each path the base branch tracks"
rule does not say what an untracked `--prompt-file`, `--system-prompt-file`
or `--skills` does (fall back or fail). The base checkout should go outside
the repository (for example `$RUNNER_TEMP`) so the agent does not see a
second copy. The fork skip needs a step output so the agent step is skipped,
since exit 0 alone does not skip later steps in a composite action. A
same-repo Dependabot pull request gets no API key, so the agent step would
fail.
