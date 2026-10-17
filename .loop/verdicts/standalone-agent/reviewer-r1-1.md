---
type: verdict
title: 'Verdict: standalone-agent reviewer round 1'
description: 'reviewer verdict for round 1 of standalone-agent: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T07:25:25+00:00'
slug: standalone-agent
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The script, its tests and the rewiring are solid, and the stamp is green.
One regression blocks the change: the audit mode no longer refuses to run on
events other than workflow_dispatch or schedule (f1). The old script enforced
that rule and ADR 0005 still states it. That matters more now that the agent
has a shell. Two smaller issues can take a plain fix: the shell time limit
leaves child processes running (f2), and the help prints contradictory
defaults (f3).

## Checked

- Ran `loopctl gate stamp` in the worktree. Result: lint, format, tests and
  integration pass; eval rows r1 to r10 pass; "stamp green:
  3a210c4d5a75252e3b70ef50bd2473abe3ec83050b37b8f293972c5837bbc420".
- Read action/agent.py, tests/test_agent.py, the test_action.py and
  test_audit.py diffs, action.yml, the workflow, knowledge-audit-issue.sh,
  ADR 0017, the corrections to ADRs 0005 and 0010, the index, the log, the
  architecture overview and the how-to diff.
- Checked each row's tests against its fails_when. r1 validates report.json
  as a Report, checks every finding's title and evidence in report.md, and
  checks the step summary. r2 covers the prompt, the prompt file, the
  default, the system prompt override and exit 2 when both prompt options
  are given. r3 covers two skill folders, the default folder and bad front
  matter. r4 covers context and skill reads, absolute and relative escapes,
  a file symlink, a directory symlink in a listing, and that search is not a
  regex. r5 covers a dropped key and tokens, the exit code, stdout and
  stderr, the output cap and the time limit; the time-limit test is weak
  (f2). r6 covers the base URL, the key, provider pass-through and an empty
  key failing before the out folder exists. r7 covers both token variables
  and the extraheader, and that the model was never called. r8 covers the
  removed files, the step order, no token in the agent step, the artifact
  and the issue path.
- Checked by hand that the composite step's
  `[ -n ] && args+=` and `while read` lines survive bash -eo pipefail when
  the inputs are empty.
- Searched the repo for leftover Hermes, knowledge-audit.sh, audit-batches,
  KMCTL_AUDIT_* and KMCTL_PLUGIN_DIR references. Only history (log, ADRs
  0005 and 0010) and the test of the removed files remain.
- r11 (judgment): read the live-run output in the scratchpad live-audit
  folder. report.json validates, with 18 findings (3 high, 15 info). Every
  finding path and every evidence path exists in the repo. The transcript
  holds no Gemini key. I accept the row.
- r12 (judgment): ran `--help` and `run --help`. Every option has a
  description, and the help names where values come from: key variables,
  GITHUB_STEP_SUMMARY, exit codes and the token refusal. The help meets the
  row apart from the contradictory defaults in f3.

## Findings

- f1 (blocking): the event guard is gone. Put it back in action.yml's audit
  step, which keeps agent.py generic, with a test in test_action.py. Or
  record the removal in ADR 0017 and in a correction to ADR 0005's
  Consequences. The first option is safer.
- f2 (not blocking): the shell time limit leaves child processes running.
  The fix is a process group, plus a test whose command has a child.
- f3 (not blocking): the generated "(default: ...)" text contradicts the
  hand-written defaults in the help.

## Notes

ADR 0005 also said the audit failed when it returned no findings. The new
correction drops that and says it fails only on an error or the time limit,
which matches the code.
