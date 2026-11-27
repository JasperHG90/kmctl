---
type: plan
title: 'Plan: adr-0057-correction'
description: Append a dated Correction to the accepted ADR 0057 that carries the PR 71 review fixes, since a stable record is never rewritten.
slug: adr-0057-correction
epic: null
depends_on: []
priority: null
schema_version: '2.0'
tags:
- plan
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T16:44:14+00:00'
---

# adr-0057-correction

Relayed from: adr-0057-pr-audit: its revision of ADR 0057 could not reach PR 71, because PR 71 merged with the record accepted on its original text; a stable record is never rewritten (`.claude/rules/okf-bundle.md`), so the fixes go in a Correction instead.

## Intent

Append one `## Correction, 2026-11-26` section to
`.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`,
which main holds as `status: stable` with Roel's no-`run_shell` rule. The
section carries what ticket `adr-0057-pr-audit` built and two reviews passed,
reworded as corrections to the accepted text, plus the operator's choice on
fetched context folders. It adds the prototype
`new:.okf/prototypes/pr-audit-scope/README.md`, with
`new:.okf/prototypes/pr-audit-scope/scope.py`,
`new:.okf/prototypes/pr-audit-scope/results.txt` and
`new:.okf/prototypes/pr-audit-scope/ref.txt`, from that ticket's branch, so
the figure the Correction cites can be run again.

Roel's no-`run_shell` rule stays in force, and the Correction says so. The
reviewed revision predates the rule, so its key reasoning is not copied: the
Correction states it in the rule's terms. Without `run_shell`, text in a pull
request cannot reach the key; an edited workflow file can, and review and
branch protection guard against that. The audit on a pull request still
works with the read, search and list tools alone.

It worked when the accepted text above the Correction is unchanged, the
Correction answers each point below, and `prek run --all-files` passes.

Measured effect: over pull request merges #60 to #75, 86 times a pull
request changed a source of a stable decision (20 distinct decisions), and
`kmctl review due --base` listed none of the 86 for that reason, because it
compares sources only for verified decisions and none is verified. Without
the Correction, the record's Context leaves out why the audit keeps its own
matcher.

## Problems

- P1: The accepted Context never says why `kmctl review due --base` (ADR 0055) does not scope the audit, or what the audit adds over it.
- P2: The accepted fork rule says the action "refuses" a fork pull request, which in `action.yml` is `exit 1` and a red check, against "never fails the check" and "a fork gets the free checks only".
- P5: The accepted text says nothing on publish when there is no report, so a fork's skipped audit, or a failed one, leaves publish failing on a missing artifact.
- P3: The accepted text presents the base-branch checkout as if it protected the run, though the pull request's own workflow file runs on a `pull_request` event; it does not say what happens to a `--context` folder an earlier step fetched, which the base checkout does not hold.
- P4: The accepted text calls the new audit "new" in one place and "fourth" in another without a name.
- P6: The accepted text does not say the merge base relies on the audit's `fetch-depth: 0`.
- P7: The accepted text does not place the feature under ADR 0046.
- P8: Copying the reviewed revision would bring back its pre-rule claim that a shell command can read the key, which reads as a Correction reversing the no-shell rule.

## Goals

- G1: A reader of ADR 0057 on main finds a record that agrees with itself, with `action.yml`, and with the measured behaviour of `kmctl review due --base`, without the accepted text being rewritten.

## Outcomes

### O1: The Correction says why `--base` does not scope the audit, with the prototype behind its figure
- kind: support
- goal: G1
- fixes: P1
- needs: none
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`, `new:.okf/prototypes/pr-audit-scope/README.md`, `new:.okf/prototypes/pr-audit-scope/scope.py`, `new:.okf/prototypes/pr-audit-scope/results.txt`, `new:.okf/prototypes/pr-audit-scope/ref.txt`, `.okf/prototypes/index.md`
- checked by: eval rows that grep the Correction for a link to ADR 0055, `review due --base`, 86 and the prototype link, and a judgment row on what the audit adds over 0055
- seen by: operator

### O2: The Correction replaces the fork refusal with a skip that exits 0 on both jobs
- kind: support
- goal: G1
- fixes: P2
- needs: none
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: an eval row that greps the Correction for exit 0 and both jobs
- seen by: operator

### O3: The Correction says what the base checkout does and does not protect, and keeps fetched context folders in the working tree
- kind: support
- goal: G1
- fixes: P3
- needs: none
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: eval rows that grep the Correction for the pull request's own workflow file and for fetched context folders, and a judgment row that it does not claim the checkout guards the key
- seen by: operator

### O5: The Correction says publish with no report posts nothing and exits 0, in every mode
- kind: support
- goal: G1
- fixes: P5
- needs: none
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: an eval row that greps the Correction for the no-report case
- seen by: operator

### O6: The Correction keeps the no-shell rule and gives the key reasoning in its terms
- kind: support
- goal: G1
- fixes: P8
- needs: none
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: eval rows that the Correction names `run_shell` as still left out on a pull request and does not say a shell command can read the key, and a judgment row that nothing in it reads as reversing the rule
- seen by: operator

### O7: The Correction states the history need
- kind: support
- goal: G1
- fixes: P6
- needs: none
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: an eval row that greps the Correction for `fetch-depth: 0`
- seen by: operator

### O8: The Correction places the feature under ADR 0046
- kind: support
- goal: G1
- fixes: P7
- needs: none
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: an eval row that greps the Correction for the ADR 0046 link
- seen by: operator

### O4: The Correction names `okf-vs-change` and leaves the accepted text above it unchanged
- kind: behaviour
- goal: G1
- fixes: P4
- needs: O1, O2, O3, O5, O6, O7, O8
- touches: `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`
- checked by: eval rows that grep for `okf-vs-change`, that the diff against main only adds lines after the last line of the accepted text, and `prek run --all-files`
- seen by: operator

## Could invalidate this plan

- none
