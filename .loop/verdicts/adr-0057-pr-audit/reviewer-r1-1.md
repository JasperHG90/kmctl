---
type: verdict
title: 'Verdict: adr-0057-pr-audit reviewer round 1'
description: 'reviewer verdict for round 1 of adr-0057-pr-audit: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-26T13:16:05+00:00'
slug: adr-0057-pr-audit
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The revised ADR 0057 answers every review point in the plan: it links ADR 0055 and says why `review due --base` cannot scope the audit (with a prototype that backs the 86 figure), skips fork pull requests with no red check, says the base-branch checkout guards the audit's honesty and not the key, names `okf-vs-change`, states the `fetch-depth: 0` reliance and places the feature under ADR 0046. Gates are green. Two wording fixes remain, neither of which needs another look.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2, r3, r5, r7, r8, r9, r10, r11 (`prek run --all-files`) and r12 all pass; "stamp green: 936a53433f0795659e28c93ff28644d77ed337340522b8697c891b8c135b5a04".
- Diff: `git diff --cached main` in the worktree, read in full: the ADR (against PR 71's original via `git show origin/adr/audit-pull-requests:...`), `.okf/decisions/index.md` (one added 0057 line, the bad union-merge line is gone), `.okf/log.md`, `.okf/prototypes/index.md`, the ack file, and the prototype's README, scope.py, ref.txt and results.txt. The `.loop/` lines in that diff are main's newer loop state, not the ticket's change.
- Facts in the ADR against the repo: `action.yml` "Check the event" exits 1 for other events (line 174-181), so the old "refuses" was a red check; `action.yml` line 41 asks audit mode for `fetch-depth: 0`; `AUDITS` in `action/agent.py:65` holds docs-vs-code, okf-vs-code, okf-vs-docs; `review_due.py:472-487` adds a sources check only when `verified_at` is set; no file in `.okf/decisions/` has a `verified:` key; `action/knowledge-ci.sh:74-95` runs `review due --base` on pull requests. No `.github/dependabot.yml`, so the same-repository-without-secrets case does not arise here.
- Prototype: results.txt lists 15 merges (#60 to #75, #71 not merged), totals 86 hits, 11 listed (all as `unverified`), 0 for a source change, 75 missed; 20 distinct decisions. The script matches its README.
- Fork handling (the plan reviewer's note): Decision lines 53-61 put the same-repository condition on both jobs, so GitHub shows them skipped; the event-check backstop skips with exit 0, and publish with no artifact posts nothing and exits 0; the ADR 0017 amendment lists the latter as a change. A fork never gets a red check. Consequences line 165 agrees.
- r1, r3, r5, r8, r9, r10, r12: each grep asserts its fails_when; read the matching ADR text, which says what the row wants (r3: lines 72-77 with folder prefix; r5: line 59 exits 0 and no "refuses"; r8: line 79; r9: line 97; r12: MERGE_HEAD is PR 71's head while the merge is staged).
- r2: grep '86' is weak (any 86 would pass) but the matching text is real, lines 30-33 and 133.
- r4 (judgment): yes. Lines 33-36: even for a verified decision `--base` only says a source changed; whether the decision still holds takes reading it against the new code, which the audit does.
- r6 (judgment): yes. Lines 65-71: the checkout keeps a pull request from loosening the audit, "It does not guard the API key", and on `pull_request` GitHub runs the pull request's own workflow file. See f2 for one overstatement.
- r7 / r7b (judgment): yes. "fourth shipped audit" is gone; the audit is named `okf-vs-change` at lines 72, 98, 103, 124, always as the shipped audit joining `AUDITS`, and the name follows the `okf-vs-X` pattern of the existing three.
- r11: `prek run --all-files` runs under the gate stamp.

## Findings

- f1 (docs, not blocking): 86 is a count of pull-request/decision pairs over 20 decisions, and `--base` listed 11 of them for another reason. The prototype README ("found 86 decisions", "found 0 of 86") and the ADR's Rejected item ("0 of the 86 decisions whose sources changed") should say it the way the Context does: 86 times, none listed for a changed source.
- f2 (docs, not blocking): the honesty claim at line 65 is stronger than the text after it allows, since the pull request can edit the workflow that does the base-branch checkout. One clause fixes it: the checkout means a loosening must show as a workflow change, which review catches.

## Notes

The primary checkout has an uncommitted edit to `.loop/plans/adr-0057-pr-audit/README.md` (the 0 of 82 to 0 of 86 rewording); the operator should commit or drop it.
