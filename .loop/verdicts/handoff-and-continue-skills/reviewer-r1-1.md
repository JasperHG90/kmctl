---
type: verdict
title: 'Verdict: handoff-and-continue-skills reviewer round 1'
description: 'reviewer verdict for round 1 of handoff-and-continue-skills: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:39:34+00:00'
slug: handoff-and-continue-skills
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The keyed update works on the happy path, and the gates and rows r1 to r4 are green. Two kmctl bugs can lose data or log entries: an empty key merges unrelated handoffs (f1), and the log dedup drops updates made on a later day (f2). The /continue evals never ran its main path, and the one pick run fails its own expectation without saying so (f3). Fail.

## Checked

- Ran `loopctl gate stamp` from the worktree. The result was "stamp green: 52958cc1e10b...". lint, format and tests passed, and rows r1 to r4 passed.
- Read the staged diff in full: src/kmctl/concepts.py, src/kmctl/__init__.py, tests/test_handoff_key.py, tests/test_skills.py, both SKILL.md files, their evals.json and results.md.
- Probed new_concept directly in a scratch bundle. `key=""` twice made the second call update the first handoff ("A work" became "B work"). An update on day +3 after a same-day repeat left no 2026-10-04 heading or line in log.md. The title '!!!' was accepted on update and refused on create.
- r1: the test asserts the same path, one file, the new description, old body text gone, dates no earlier than before, one index entry and exactly one new log line. Its date checks use >=, which is weak but acceptable because the test uses the real clock.
- r2 and r3: the tests assert handoff_key on a new handoff, and strict okf validation plus kmctl check on the bundle.
- r4: the test checks that the prose names the condition. It cannot check agent behaviour, which f1 covers on the kmctl side.
- r5 (judgment): continue/SKILL.md uses AskUserQuestion with multiSelect true, three newest plus more, reads only the chosen paths, and ends with a question, taking no action first. The plain-text list only applies when AskUserQuestion is missing. The text meets the row. The runs do not show it (f3).
- r6 (judgment): both skills have evals.json and results.md. I opened the workspace at iteration-1/continue-pick/with_skill/outputs/summary.md. It lists 4 handoffs and no more option, and no run loads or summarizes a choice (f3). The handoff runs match results.md: one file stays in place and log.md has one Updated line.
- Consistency: ADR 0009 and manifesto I4 agree with the handoff_key field. docs/ has no CLI reference that needs --key.

## Findings

- f1 (bug, blocking): refuse an empty or blank --key in new_concept with a ConceptError, and give a test. The skill should also show the conditional form in its code block, for example `${CLAUDE_CODE_SESSION_ID:+--key "$CLAUDE_CODE_SESSION_ID"}`, so copying the line cannot pass an empty key.
- f2 (bug, blocking): either drop the dedup and log every update, as r1 says, or limit it to a matching line under today's heading. test_repeated_update_logs_once should then cover the cross-day case. This changes the log contract, so it needs a second look.
- f3 (missing, blocking): add or rerun a continue prompt that picks handoffs, for example a prompt that names the choice up front, so step 3's combined brief is tested. Report every evals.json expectation in results.md, including the failed "three plus more" one for the fallback run. Or change the fallback so it also offers three plus more.
- f4 (hardening, not blocking): run the same title check on the update path. It is a one-line fix I trust without a second look.
