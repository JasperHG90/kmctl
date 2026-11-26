---
type: verdict
title: 'Verdict: action-failure-points-to-summary reviewer round 1'
description: 'reviewer verdict for round 1 of action-failure-points-to-summary: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-26T13:24:02+00:00'
slug: action-failure-points-to-summary
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. When kmctl check fails or kmctl review due crashes, action/knowledge-ci.sh now prints one `::error title=kmctl::` line to stdout. The line names the failed command and points at the run's summary page, linking to it when GITHUB_SERVER_URL, GITHUB_REPOSITORY and GITHUB_RUN_ID are set and adding `/attempts/N` when GITHUB_RUN_ATTEMPT is set. The exit status is unchanged. The tests assert each row's fails_when, and the gates pass.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree myself. Result: lint, format, tests, integration and eval rows r1 to r4 all pass, "stamp green: 5460d3dfb456d203eafb288097212ce1689f4d2addc5e8d9fd7503846953e989".
- Code: I read action/knowledge-ci.sh in full. `failed=()` and `${#failed[@]}` are safe under `set -u`, even in bash 3.2. `failed[1]` is read only when the array holds more than one entry. The `&&` short-circuits cannot change the exit status, because the script has no `set -e` and `exit "$status"` is unchanged. The message has no `%`, CR or LF, so no workflow-command escaping is needed. The `/actions/runs/ID/attempts/N` URL is a valid GitHub run page and shows the job summaries.
- r1: test_script_prints_error_line_when_check_fails runs a broken bundle with the run variables set. It asserts a nonzero exit, exactly one ::error line, "kmctl check failed", "summary page" and the full expected URL. A wrong or missing link, a missing line or exit 0 would each fail it.
- r2: test_script_prints_error_line_when_review_due_crashes uses the crashing stub. It asserts a nonzero exit, one line, "kmctl review due failed" and the URL.
- r3: test_script_prints_no_error_line_when_passing asserts that a passing run prints no ::error line. test_script_prints_error_line_without_run_url sets the run variables to empty, which overrides any inherited CI values. It asserts the line still appears, says "summary page", and contains no "http" and no "/actions/runs/".
- r4: the how-to at docs/how-to/install-the-plugin-and-the-ci-action.md:219 says "a link to the run's summary page", and its example matches the script's output. The other docs that mention the job summary are still true.
- Checklist: review start printed no checklist lines.

## Findings

None.

## Notes

- The script prints no ::error line when GITHUB_STEP_SUMMARY is unset, because the summary then goes to stdout and the reasons are already in the log. That fits the intent. Row r3's "outside GitHub" means the run variables are missing, not GITHUB_STEP_SUMMARY, and the test sets GITHUB_STEP_SUMMARY.
- No test covers the case where both commands fail, which produces "kmctl check and kmctl review due failed". The eval does not ask for one, and the code path is plain.
