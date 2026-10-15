---
type: verdict
title: 'Verdict: briefing reviewer round 1'
description: 'reviewer verdict for round 1 of briefing: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:54:06+00:00'
slug: briefing
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `kmctl briefing` prints routing, counts-only state and the packaged rules without their WHY lines. It prints 424 words on this repository, works in an empty folder and names `kmctl init` there, writes nothing, and `--json` returns one object. The wheel ships both rule files. The only real gap is that the r1 test does not catch a missing routing part (f1). f2 and f3 are small cleanups. All three are plain fixes, so none blocks.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, eval rows r1 to r6 pass, "stamp green: ea737929a3d3be5cc32f8e767f63ee7c23455b6a9d40c5abcb82023aec89d1f3".
- I read the staged diff (`src/kmctl/__init__.py`, `briefing.py`, both rule files, `tests/test_briefing.py`) in full.
- I ran `kmctl briefing` on this repository (424 words, exit 0), on an empty folder (the init hint plus the rules), and on a fixture with a broken concept file. The broken file did not crash it because review_due skips bad front matter.
- I built the wheel with `uv build --wheel` and found `kmctl/rules/docs-layout.md` and `okf-bundle.md` in it.
- Every verb named exists: init, new with five kinds, check, review due, handoffs. Each takes --help and --json. `kmctl new` writes the dated log line that the kmctl-writes-the-structure rule claims. `kmctl init` writes docs/README.md, which the routing names.
- Eval rows. r2: the fixture has 1 concept due (manifesto) and 2 handoffs, and the test compares both against `review due` and `handoffs`, so the manifesto-name check means something. r3: the fixture has a due concept and handoffs. r4, r5 and r6 assert their fails_when. r1 is weak (f1).
- Consistency: the help follows the existing --path/--json pattern and has a one-line docstring and an epilog. This matches ADR 0002 and the manifesto's I3. Routing names no skills, which is right because no plugin skills ship yet.

## Findings

- f1 (test-strength, non-blocking, row r1): the routing check also matches text from the rules part. A one-line assertion change fixes it, and I trust that without a second look.
- f2 (nit, non-blocking): the WORD_BUDGET constant is unused, and the test hardcodes 600.
- f3 (nit, non-blocking): "1 concepts" in the state line.

## Notes

The work is staged but not committed on loop/briefing. I left manifesto I3 at "Status: planned" because no earlier ticket updated invariant statuses.
