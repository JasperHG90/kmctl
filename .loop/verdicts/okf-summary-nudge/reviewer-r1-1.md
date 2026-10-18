---
type: verdict
title: 'Verdict: okf-summary-nudge reviewer round 1'
description: 'reviewer verdict for round 1 of okf-summary-nudge: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T23:29:12+00:00'
slug: okf-summary-nudge
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. The verb, the hook entry, doctor's
check, ADR 0028 superseding ADR 0004, I1 and the docs agree, and every eval
row's test checks its fails_when. I re-ran the stamp myself and it is green.
Three non-blocking findings remain: empty stdin should fall back to --path,
the verb has no --json, and one sentence on the explanation page is wrong.
None of them needs another review round.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and rows r1 to r6 all pass; "stamp green: 1e97a239a6c0923bfb08bed18549840ec35b42832d9c2f2e7df97f787f176bd3".
- Read the full diff of summary.py, __init__.py, plugin.py, antigravity.py, doctor.py, hooks.json, the tests, ADR 0028, the ADR 0004 correction, the manifesto, overview, summary, README, rule and docs pages.
- r1: the tests assert the JSON keys exactly, the concept id and both ways out, and exit 0. r2: the tests cover the current summary, an edit, an ack, the log, index, decisions/index, handoff and summary-only cases, a repeated set, a grown set, outside git, no bundle, five bad stdins, no writes under .okf/, KMCTL_PINNED in the command, and a fake old kmctl. I mutated the uvx test in a scratch copy (dropped KMCTL_PINNED=1) and it failed, so it bites. r3: review_due is patched to raise in every kmctl module that holds it. r4: the tests check the package entry against package_hooks, the command run with no kmctl on PATH, and doctor passing, missing and changed. r5: the decision is marked superseded, I1 is checked, and the three pages are checked.
- By hand, in a scratch repo made with kmctl init: after `kmctl new decision` the claude format named decisions/0002-use-x and both ways out. A repeat printed {}. After commit, ack and commit, edits to only log.md and index.md printed {}. The state is .git/kmctl/summary-nudge. In a linked worktree, `git rev-parse --git-path` gives .git/worktrees/NAME/kmctl/summary-nudge, and from a subfolder it gives a path relative to -C, which `root /` handles. Nothing else is written.
- Hook shell: `command -v` reads no stdin, so the payload reaches kmctl. stderr is dropped and `|| echo '{}'` covers the old copy's exit 2, which writes its usage only to stderr. The command always ends with exit 0.
- Summary: exactly 500 body words by body_words, which is within the limit. It is still holistic: it gains one sentence on the PostToolUse hook and two tightened sentences, and lists no decisions.
- Judgement calls: (1) a hash over the summary bytes and the ids is sound; a shrunk set nudging again is rare and harmless. (2) quiet on empty stdin: see f1. (3) no --json: see f2. (4) no tool_input filter: matches the plan's intent ("when the freshness rule says the summary is behind"), and it nudges at most once per set per git directory. (5) catching OSError and ValueError covers git missing (FileNotFoundError), a decode error, BadPayload and state write errors. (6) keeping the explanation page's filename avoids breaking links; the title and every link text changed.

## Findings

- f1: confirmed by hand. `kmctl summary nudge --path . </dev/null` in a repo whose summary is behind printed nothing and exited 0, while the same repo with a payload on stdin nudged. Falling back to --path when stdin gives no cwd would match briefing. Non-blocking because the hook path, the one the plan targets, works.
- f2: the repo rule names --json for every verb that prints results. Non-blocking: the fix is additive or a recorded exception.
- f3: a one-sentence docs fix.

## Notes

Two parallel tool calls can both read the old state and both nudge once. That is harmless and needs no fix. The summary's line "the kmctl on PATH hands every command to that release" is now slightly loose because of the nudge's KMCTL_PINNED, but it is fine at summary depth.
