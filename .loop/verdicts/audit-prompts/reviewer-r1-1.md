---
type: verdict
title: 'Verdict: audit-prompts reviewer round 1'
description: 'reviewer verdict for round 1 of audit-prompts: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T17:47:26+00:00'
slug: audit-prompts
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `--audit` picks one of three shipped prompt files, and `okf-vs-code` is the default. It cannot be combined with `--prompt` or `--prompt-file`. `action.yml` gains `audit` and `report_name`, and the workflow runs audit and publish as matching matrices with their own artifacts and issue titles. The three prompt files match the spike files byte for byte. One user doc, the explanation page on report-only audits, still tells readers that the CI audit checks only the concepts that are due and posts to a single issue. That is the misreading r4 guards against, so it needs a plain docs fix. It does not need another round.

## Checked

- Ran `loopctl gate stamp` from the worktree: lint, format, tests and integration all pass, and eval rows r1, r2 and r3 pass. Result: "stamp green: e144a992ad09857c0261d6ea1ae79eeb7232ed60cd0f7d22a1ab2d95ee56f307".
- Diffed the prompts against the spike files. `action/prompts/docs-vs-code.md` and `okf-vs-docs.md` are identical to `.loop/spikes/audit-prompts/1/files/*.md.txt`, and `okf-vs-code.md` is identical to `spike 2/files/okf-vs-code-r2.md.txt`.
- r1: `test_audit_option_sends_its_prompt` is parametrized over all three names. It asserts that each file is non-empty and that the recorded user message equals the file's text. It would fail if a file were missing or empty, or if the wrong text were sent.
- r2: the default test asserts the message equals `okf-vs-code.md` exactly. The combination tests cover `--prompt` and `--prompt-file` and check exit 2 with both flags named on stderr. The unknown-name test checks argparse's exit 2, and the help test checks all three names and the default. Each assertion matches its fails_when.
- r3: the workflow tests assert the audit matrix (`fail-fast` false, all three names), the `--audit ${{ matrix.audit }}` arg and the per-audit artifact name on both upload and download. On publish they also assert the `!cancelled()` condition, the publish include matrix with the same audits in the same order, distinct non-empty titles, and `--title`. The no-token and no-cache checks are kept. The action tests assert the `--audit "$AUDIT"` arg, `report_name` on both upload and download, and the default `agent-report`.
- Correctness: the mutual-exclusion check runs before any work. The action passes `--audit` only when the input is set, so the action's default falls through to `okf-vs-code`. A failed audit leg that wrote no report uploads nothing (`if-no-files-found: ignore`), so its publish leg fails on download while the other legs still publish. That is what the plan says should happen. Severity guidance still lives in the system prompt (high, medium and so on), so dropping the old prompt's drifted-to-high mapping leaves `--min-severity high` publishing meaningful.
- r4 (judgment): I read how-to section 5. It names the three audits and the default, gives the `audit` and `report_name` input rows, and adds an "All three audits" paragraph. It no longer says the default checks only concepts that are due. The tutorial now points at `--audit` and `action/prompts/`. ADR 0017 has a dated correction that agrees with the code, and the overview diagram shows `action/prompts/` with the edge to the CLI. All of this is consistent with the code. The one gap is f1.
- Grepped docs/, README.md and the code for leftover mentions of the old default prompt, the auditor and "due". Only the explanation page is stale. The README's "/audit" lines describe the in-session skill, which still exists.

## Findings

- f1 (docs, not blocking): lines 28-34 of `docs/explanation/why-one-hook-and-report-only-audits.md` say "A separate agent checks the knowledge that is due ... In CI it runs with the same limit, and its findings go to the job summary and one 'Knowledge audit' issue." That held for the old default. Now the CI audit checks all of `.okf/` and `docs/` as three audits with three issues. "The same limit" (read and search tools only) was already false for the CI agent, which has `run_shell`. Fix: keep the sentence about the `/audit` skill checking the knowledge that is due, and say that in CI the agent runs the three shipped audits (all concepts, docs against code, docs against .okf/), reports only, and posts each audit's findings to its own issue. A reader of this page would otherwise come away with the misreading in r4's fails_when.

## Notes

- The checkout comment in the workflow and in the how-to's example ("full history for review due") no longer describes what the default audit uses. It is harmless, since the agent can still run kmctl, and a later edit could reword it.
