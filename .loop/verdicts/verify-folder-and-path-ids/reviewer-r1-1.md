---
type: verdict
title: 'Verdict: verify-folder-and-path-ids reviewer round 1'
description: 'reviewer verdict for round 1 of verify-folder-and-path-ids: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-27T10:13:08+00:00'
slug: verify-folder-and-path-ids
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. A folder id verifies every page under it
that `kmctl review due` lists, and the page set comes from the new shared
`kmctl.pages` module. Repository-root paths work. `decisions/index`, `log` and
`handoffs` are refused. Refusals for `decisions/*` and `decisions/index` name
`kmctl verify decisions`. One small spelling bug remains: `.okf/docs/...` is
read as a docs page. The fix is plain, so it does not need to come back to me.

## Checked

- Gates: I re-ran `loopctl gate stamp` from the worktree. Lint, format, tests,
  integration and rows r1 to r6 all passed: "stamp green:
  94165b734effec3063cf1e90555234d687aedc49d2e6bc153fa7636cb2c493d6".
- Code: I read `pages.py`, the `verify.py` diff (`_pages`, `_folder_hint`,
  `_targets`, `--by` moved into `verify_all`, dedup by canonical id), the
  `review_due.py` move, and the CLI help and epilog.
- Probes in a scratch repo: `./decisions/0001-a` and `decisions/../decisions`
  are refused with the canonical spelling. `decisions/*` gets the folder hint.
  `.okf` and `docs` are refused. `.okf/docs/how-to/run.md` is accepted and
  writes `docs/how-to/run.md` (f1).
- r1: the test checks exit 0, three ids, an entry on each record, three log
  lines, the index byte for byte, and that the manifesto is untouched. Its
  three cases cover `decisions`, `decisions/` and `.okf/decisions`.
- r2: the test checks both pages get entries, and that `README.md` and a page
  outside the folder stay unchanged.
- r3: the test asserts the printed id for `.okf/decisions/0001-a.md`,
  `.okf/manifesto.md` and `docs/how-to/run.md`. The ids are hardcoded, but they
  are the ids review due prints.
- r4: the test checks exit 1, empty stdout, a single refusal line, and that no
  file in the repo changed. It covers `decisions/index`,
  `.okf/decisions/index.md`, `log`, `handoffs`, `.okf/handoffs/`, a README and
  a prototype non-README.
- r5: the test asserts `kmctl verify decisions --by human:jasper` is on stderr
  for `decisions/*`, `.okf/decisions/*`, `decisions/index` and a missing id.
- r6: the help test asserts the folder form, the `.okf/...md` path form and
  the folder example. `test_help.py` passes.
- r7 (judgment): ADR 0059 exists as a draft. It states the folder form and
  explains why it does not undo ADR 0055's `--base` rejection: the person
  types the folder name, while `--base` picks pages by what a branch changed.
  It is linked from `decisions/index.md`, and ADR 0055 has a dated correction
  that links it. Pass.
- Consistency: `docs/reference/commands.md`, both okf-bundle instructions, the
  `OLD_RULES` hash and its comment, and the `verify_all` docstring all match
  the code. `.claude/rules/okf-bundle.md` only mentions verify for the
  summary and `verified` entries. It never describes id forms, so leaving it
  unchanged is right.
- No checklist lines were printed for this round.

## Findings

- f1 (bug, non-blocking): `cid = given.rstrip("/").removesuffix(".md").removeprefix(".okf/")`
  runs before `docs = cid.startswith("docs/")`, so `.okf/docs/how-to/run.md`
  verifies `docs/how-to/run.md`. It also makes a concept folder named
  `.okf/docs/` unreachable. Fix: refuse the id when what is left after
  stripping `.okf/` starts with `docs/`, or strip `.okf/` only for the
  concept branch. Add a refusal case to the r4 test.

## Notes

- `kmctl verify docs` is refused with "at .okf/docs(.md)", which reads oddly.
  The plan does not ask for the whole docs folder, so this is not a finding.
- `_pages` walks the tree once per argument. A glob over 59 records walks it
  59 times. That is fine at this size.
