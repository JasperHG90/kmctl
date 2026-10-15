---
type: verdict
title: 'Verdict: write-docs-skill reviewer round 1'
description: 'reviewer verdict for round 1 of write-docs-skill: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:25:34+00:00'
slug: write-docs-skill
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The skill does what the plan asks: it routes by reader intent to one of four
types, creates pages only through `kmctl new doc`, leaves the folder, skeleton
and index to kmctl, and ends with `kmctl check`. Every verb and option it names
exists. Two non-blocking defects sit in the eval artifacts kept beside the
skill: a broken benchmark file and grading that is not kept.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval-row r1
  pass; "stamp green: a47445b2347fd2d952c08e000b1dd9916771d3b02da94cfe79ea1cc936ca34c1".
- r1: tests/test_skills.py::test_write_docs_skill_layout reads SKILL.md (fails
  if missing) and asserts each of the four reference files is a file, so it
  fails when the row's fails_when holds.
- r2 (judgment): SKILL.md step 3 says to run `kmctl new doc TYPE 'Title'
  --description ...` and "Do not create the file, the folder or the index entry
  yourself"; step 4 fills only the skeleton's sections. Nothing tells the agent
  to write front matter or an index entry. Holds.
- r3 (judgment): evals/evals.json holds four prompts, one per type; results.md
  records skill-creator iterations 1 and 2. I opened the run workspaces: every
  with-skill and baseline page landed in its type folder (docs/tutorials,
  docs/how-to, docs/reference, docs/explanation), and each grading.json shows
  4/4. The iteration-2 tutorial takes the install command from the repo and
  leaves a TODO where no source exists, as results.md says. Holds.
- Verbs against the CLI: `kmctl new doc --help` (TYPE, TITLE, --description),
  `kmctl new decision|proposal|prototype|handoff`, `kmctl init`, `kmctl check`
  all exist. The refusals step 3 maps (missing docs/README.md, page exists)
  match src/kmctl/docs.py.
- Reference files agree with the skeleton sections in src/kmctl/docs.py and
  with .claude/rules/docs-layout.md's type definitions.

## Findings

- f1: iteration-1-benchmark.md is the skill-creator aggregate run that found no
  grading data, so it shows placeholders and zeros. It contradicts results.md.
  Non-blocking: delete it or regenerate it with real data; either plain fix is
  safe.
- f2: ADR 0007 says to keep the test prompts so a reviewer can check them;
  the prompts are kept, but the four scripted checks behind "4/4" are not.
  Add them as `expectations` in evals.json (or keep grade.py beside the
  skill). Non-blocking: it strengthens evidence and changes no behavior.

## Notes

Step 1 lists `kmctl new decision|proposal|prototype|handoff` and leaves out
`practice`; that is a routing choice, not a defect.
