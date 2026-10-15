---
type: verdict
title: 'Verdict: audit-hermes-hardening reviewer round 1'
description: 'reviewer verdict for round 1 of audit-hermes-hardening: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T16:10:15+00:00'
slug: audit-hermes-hardening
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. The audit runs once per batch of at most
ten concepts of one kind, with only that kind's review skill. KMCTL_AUDIT_TIMEOUT
is one budget for the whole audit, and HERMES_MANAGED_DIR is cleared. The gates
and all five rows are green. One small bug remains: the merged block can break
when a finding's text holds an escaped triple backtick (f1). The plain fix is to
escape backticks when writing the merged block, such as
`.replace("`", "\\u0060")` on the json.dumps output, plus a test for it. I do
not need to see that fix again, so the label is fix.

## Checked

- Ran `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1, r2, r3, r5 and r4 pass, and it ends "stamp green: 39775c59fdcb9f73c8a31af426380162a53488a6f31f214ebad4e2b54f5fc305".
- Read the staged diff and every changed file in full: action/audit-batches.py, action/knowledge-audit.sh, tests/test_ci_audit.py, the how-to and .okf/architecture/overview.md. Also read action/audit-report.py and plugin/skills/audit/SKILL.md.
- Guards: the event refusal, the GH_TOKEN/GITHUB_TOKEN and extraheader refusals, the model and base URL checks, the timeout parse and the key-variable checks all run before review due and before any Hermes call. The unset of the five HERMES_* variables comes before the loop, so every run is covered.
- Budget: the value must match `^[0-9]+[smhd]?$` and is read with base 10, so leading zeros work and anything else is refused with a message naming the value. A budget of 0 means left = 0, and the audit fails at once naming every batch, so it never reaches `timeout 0`, which would mean no limit at all. A value cannot be negative. A run cut off by timeout (124 or 137) names its own batch and the ones after it. The builder's choices are fine: starting the clock at the first run, rounding to whole seconds (under one second of slack), and stopping at the first failing batch, which matches the plan's "fails the step". With the 30s kill-after, the default 30m still ends well before timeout-minutes 40.
- importlib: the path is Path(__file__).with_name("audit-report.py"). __file__ comes from "$here", the action's own folder, so the audited repository cannot redirect it. Run as a script, Python puts the script's folder on sys.path, not the cwd.
- Prompts: each holds the absolute `pwd -P` repo path, one batch file, the audit skill, the auditor text and one review skill. r1 checks this for each call, including that the other kinds' skills are absent.
- Merged block: one fenced json list in the auditor's shape, checked again with audit-report.py's _findings. Each batch's reply goes through the same checks. An empty list passes, as before.
- Rows: r1 checks 4 calls (2, 1, 1), one kind per call, at most ten ids, prompts under 64 KiB, and all 25 concepts in the summary and the body. r2 has the second call print no block, then checks the batch name in stderr and the summary, the stop after two calls, and that no body was written. r3 records the stub's environment. r5 uses a 3s budget with a 2s sleep, checks the elapsed time is under 15s, a non-zero exit, "time limit", the two unfinished batch names and no body. None of them pass while the behaviour is broken.
- Docs: the overview's diagram, text and Depicts list now match the script. The how-to's new line and the header comment are accurate. action.yml and the workflow's 30m stay true. Nothing else in docs/ or .okf/ still says one session audits every batch.
- Reproduced f1 in the scratch folder: a reply whose summary holds ``` passes add, and a second add then fails with "Unterminated string".

## Findings

- f1 (bug, not blocking): add calls json.dumps(earlier + new), which leaves backticks as they are. A finding string that decodes to ``` ends the fence early in the merged file. The next add then fails with "the decisions batch ... gave no usable findings", blaming a batch that answered correctly, or audit-report.py fails on the last one. The audit fails loudly rather than reporting something wrong, and the fix is one line plus a test, so I do not need to see it again.

## Notes

- A fractional value such as 1.5m used to be accepted, because timeout took it, and is now refused with a clear message. The docs only show whole values, so this is fine.
