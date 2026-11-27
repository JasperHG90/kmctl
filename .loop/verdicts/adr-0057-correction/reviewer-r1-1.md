---
type: verdict
title: 'Verdict: adr-0057-correction reviewer round 1'
description: 'reviewer verdict for round 1 of adr-0057-correction: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-26T17:13:57+00:00'
slug: adr-0057-correction
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The Correction is appended below the accepted text, which is byte-identical
to main. It keeps the no-shell rule, and its claims match action.yml,
action/knowledge-ci.sh, action/agent.py and review_due.py. The prototype
matches its source branch exactly. One wording issue remains: "in every
mode" in the no-report sentence has no clear meaning. It should be fixed now,
because a stable record only takes another Correction later. It does not
block.

## Checked

- Gates: `loopctl gate stamp` from the worktree gave "stamp green:
  40d9a026...". lint, format, tests and integration passed, and so did eval
  rows r1, r2, r3, r5, r6, r8, r9, r10 (prek run --all-files), r11 and r12.
- The accepted text is unchanged. `git show main:<adr>` is byte-identical
  (cmp) to the first 139 lines of the worktree file. The only `^-` line in
  the diff is the `---` header. Status stays stable.
- r4 (judgment): passes. "Even for a verified decision, `--base` says only
  that a source changed. Whether the decision still holds after the change
  takes reading it against the new code, which is what the audit does."
- r7 (judgment): passes. The Correction says the base checkout "does not stop
  that", that it only makes loosening the audit visible, and that the key is
  out of reach "because the agent runs without `run_shell` ... not because of
  the checkout."
- r13 (judgment): passes. The opening says "the no-shell rule stays in
  force". The key paragraph cites run_shell's absence "as the rule above
  decides". It drops the pre-rule "a shell command can read the key" claim.
  Saying a same-repository author can change the workflow repeats what the
  accepted Consequences already say (branch protection and review guard
  against that). No sentence gives the agent a shell or makes the rule
  conditional.
- Claims against the code:
  - knowledge-ci.sh runs `kmctl review due --base origin/$GITHUB_BASE_REF`
    on a pull request ("shows that list on every pull request").
  - review_due.py adds `_Check`s (source comparison) only when
    `verified_at is not None`, and appends `unverified` otherwise.
  - AUDITS in action/agent.py holds three audits.
  - action.yml documents audit mode asking for persist-credentials: false
    and fetch-depth: 0.
  - Today's "Check the event" step exits 1 on other events, so "skipped, not
    refused" correctly changes the planned fork behaviour.
- Prototype: `git diff --cached loop/adr-0057-pr-audit -- .okf/prototypes/pr-audit-scope/`
  is empty. The totals in results.txt (86 hits, 0 for a source-change reason,
  20 distinct decisions per README) match the Correction. The index line was
  added.
- Ack: old ack removed, new ack names 0057 and the prototype.

## Findings

- f1 (docs, non-blocking): at line 174 (the fork paragraph), "When there is
  no report, publish posts nothing and exits 0, in every mode". Publish is a
  mode, so the phrase reads oddly. Name what is meant, for example "whether
  it would post an issue or a pull request comment".

## Notes

- Row r9's command, `! git diff main -- ADR | grep -q '^-[^-]'`, cannot see a
  removed bullet line. The accepted text has many lines that start with "- ",
  and a removed one shows in the diff as "-- ...", which the pattern skips.
  So the row would pass if a bullet in the accepted Decision were deleted.
  I checked the behaviour directly with a byte compare (above), so this
  round is fine. The operator may want to tighten the row's command (for
  example, compare `git show main:FILE` with the file's head) the next time
  a Correction ticket reuses it.
