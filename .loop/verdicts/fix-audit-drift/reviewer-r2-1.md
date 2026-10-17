---
type: verdict
title: 'Verdict: fix-audit-drift reviewer round 2'
description: 'reviewer verdict for round 2 of fix-audit-drift: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T19:36:24+00:00'
slug: fix-audit-drift
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round-1 findings are fixed. The two new tests in tests/test_docs.py guard row r2: they fail against HEAD's src/kmctl/__init__.py and pass on this tree. The README and the briefing docstring no longer say the briefing gives the writing rules. The hook description went to the follow-up stub, which is fine for a non-blocking docs finding. The r4 rerun exists and is sorted correctly. The tutorial now quotes the tut4 reruns word for word, and the gates are green.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration, r1 and r2 all pass. Stamp green, 3d3885f21df26c89fb258454ced39c7732f58b6b0f545c69d51bfee007e4fcd6.
- f1: I copied the tree to the scratchpad and put HEAD's src/kmctl/__init__.py back. Both `test_reference_rows_quote_the_help_they_summarize` and `test_reference_new_json_keys_match_the_help` then fail, the first on the review due and briefing rows and the second on the missing `updated` key. Both names match r2's `-k "help or commands or reference"`, so the row's command runs them.
- f2: the README diff at lines ~10 and ~195 and briefing.py's docstring now say "which skills to use" and "one reading rule". That matches the briefing output I checked in round 1. The stub `.loop/plans/audit-drift-followup.md` names HOOK_DESCRIPTION and hooks.json.
- r4 sorting: I listed all 17 findings in the three `out-*/report.json` files and compared them with spikes 2 to 4. Five of them overlap the 35. overview.md:167 and :209 are fixed in the diff, with the plugin patch row and the "What kmctl adds" bullet. why-one-hook.md:18 is fixed: it now says "kmctl's own hook", and a new paragraph covers okf's Stop hook. install-kmctl-with-apm.md:44 is something the repository cannot settle, so "not real" is the right call. The audit tutorial's stale line numbers were caused by this ticket's edit to commands.md, so fixing them here is fair. The other findings are new claims, not ones that came back: ADR 0001:59-60 is the wheel claim, not the plugin install claim the 35 named, and ADR 0012:90-93 is not the description at :4. Every one of them is listed in the stub.
- Tutorial quotes against `tut4/report/report.md` and `report2/report.md`: the summary, the severity count, the table row (minus the Summary column), the `--path` checked item ("seven things") and the second run's summary and row all match word for word apart from rewrapping. In the worktree, commands.md:257 is the `--json` row, so the planted line really is 257. In tut4/kmctl, `grep -n as-json` prints line 257, the same as step 3. get-started line 29 is still the inline `kmctl --version`. The tutorial dropped the "Your clone also has this page" caveat. That is right, because the quoted run now reports on that page.
- Scope: the diff grew from 19 to 23 files: README.md, src/kmctl/briefing.py, tests/test_docs.py and the audit tutorial. Each traces to f1, f2 or r4.

## Findings

- f1: resolved. tests/test_docs.py:110-133 asserts that the help and the reference rows agree, that review due names docs/, that briefing names its reading rule, and that the `new --json` keys match. All of these fail on the old help.
- f2: resolved. README.md and src/kmctl/briefing.py:1 are fixed. The hook description is tracked in the audit-drift-followup stub.

## Notes

README.md:11 is now one long unwrapped line ("to use; the rules for writing knowledge come with its package. Its GitHub Action..."), unlike the paragraph around it. Row r3 still needs the commit message to exist before it can be judged.
