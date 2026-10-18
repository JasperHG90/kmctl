---
type: verdict
title: 'Verdict: starter-reviewer-gitignore reviewer round 1'
description: 'reviewer verdict for round 1 of starter-reviewer-gitignore: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T18:51:20+00:00'
slug: starter-reviewer-gitignore
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. With the default answer, AGENTS.md gets the adversarial-reviews rule word for word from jasperhg90/skills at 41f49502. apm.yml gets the pinned `.agent.md` entry only when claude is a harness. Answering false writes neither. The .gitignore holds every listed path and none of the committed ones. The docs match the change. One test assertion is vacuous, and a plain fix is enough, so the verdict is fix.

## Checked

- Ran `loopctl gate stamp` from the worktree: lint, format, tests and integration all passed, and so did eval rows r1 to r7. Result: "stamp green: b557d3ecf85e0e6cadaf0b57f0a44ba7ee9615677a01ae8fc0122f0957010cd4".
- Fetched rules/adversarial-reviews.instructions.md at 41f495021f3b264992c8fa764d58565c1184ab91 with `gh api` and compared it to the constraint block in starter/AGENTS.md.jinja. They match exactly.
- Rendered the template by hand (defaults with a description, and adversarial_review=false). The section's spacing is right, apm.yml parses with the comment inside the list, and the off render leaves AGENTS.md without the section.
- Rows: r1 checks four phrases from the rule and that the answer is `True`. r2 checks `deps[1:]` exactly against `[REVIEWER]` or `[]` for every harness set, so a missing entry, an unpinned one or one pinned to another commit fails. r3 checks the whole dependency list and that "adversarial" is absent from AGENTS.md. r4 runs `git check-ignore --no-index` and compares the results as sets in both directions. r5 adds the `.claude/agents/adversarial-reviewer.md` check to the bootstrap test, which renders with the defaults for all three harnesses. r6 covers the how-to table and the README section. Each test fails when its row's `fails_when` happens.
- Loosening `test_render_writes_the_project_pinned_to_this_release` to `[0]` loses nothing, because the r2 and r3 tests pin the full list.
- Consistency: the copier help, the how-to rows and the README agree with the plan and with ADR 0024 (OpenCode skips the Claude-format copy, Antigravity gets nothing). The manifesto and overview describe the starter at a level this change does not make false.

## Findings

- f1 (test-strength, non-blocking): the `"agents/adversarial-reviewer.md\n" not in section` check in the README docs test can never fail, because the section's whitespace was already collapsed. The other two assertions in that test do work.
