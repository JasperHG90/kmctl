---
type: verdict
title: 'Verdict: decision-gaps-skill plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of decision-gaps-skill: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T16:16:17+00:00'
slug: decision-gaps-skill
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: the skill folder reaches all three harnesses with no
extra wiring, the wheel and briefing pick it up from the folder, a how-to
page is the right kind of page, and Problems, Goals and Outcomes match the
prose. Two things need a revision. First, the plan follows the prototype but
judges every change in one session, which is not what the prototype measured,
and it says nothing about long ranges (p1). Second, two install pages still
say kmctl has seven skills and are left out of the plan's scope (p2).

## Checked

- Harnesses: kmctl's apm.yml ships everything under `.apm/skills/`. APM
  copies each skill folder into `.claude/skills/` and `.agents/skills/`.
  `opencode.py` and `antigravity.py` translate only agents and rules, and
  OpenCode reads skills from `.agents/skills/`. The integration test loops
  over `SKILL_NAMES` (test_apm_package.py:70), which the plan touches. A new
  folder needs nothing more.
- Wheel: `hatch_build.py` force-includes the whole apm folders, and
  `test_wheel_reports_the_set_version_and_carries_the_skills` walks every
  file under SKILLS, so a new skill and its `evals/` ship with no change.
- Briefing: `load_skills()` reads `plugin.skills_dir()` at run time, and
  `test_briefing_names_every_skill` already covers any folder. In the worst
  case (long handoff, summary 100 behind), the token-budget test now comes to
  456 of 500 (I measured it with the test helpers). One more 12-word summary
  line adds about 25, so it still fits, with little room left.
- Docs: `docs/how-to/` fits per docs-layout.md, since this is one task done
  one way. `docs/how-to/README.md` is generated, so `kmctl check --fix`
  writes that touch.
- Eval rows: all three run pytest commands. r3's `-k 'how_to or migrated'`
  picks `test_this_repo_docs_are_migrated` from test_docs_frontmatter.py
  today, and the new test file's names decide the rest.
- Dependency: decision-candidates' worktree has the verb with `--since` and
  `--json`. Its JSON fields (sha, parent, kind, subject, message, slug,
  plan, files, recorded, signals, score) give the skill what the plan has
  it read: the parent for the earlier index, and `recorded` for covered.
  ADR 0047 states the report-only split the plan builds.
- Facts: there is one behaviour outcome, which fixes P1 and serves G1, and
  its touches cover the prose's skill, evals, tests, docs and help (but see
  p2 and the note on `__init__.py`).
- Rules: skills-are-thin, skills-via-skill-creator, cli-version-floor
  (skills-name-only-shipped-verbs holds through depends_on) and
  prompts-may-code-must. Judging is the kind of call that belongs in a
  prompt.

## Findings

- p1: one-session judging of every change is untested against the
  prototype's per-change judging, and there is no plan for long ranges. The
  eval should cover a range with known answers.
- p2: the "seven skills" lists in two install how-to pages go stale and are
  not in scope.

## Notes

- The dependency already names the decision-gaps skill in the `candidates`
  epilog and in `--json`'s help (worktree `__init__.py` ~938-985). So the
  plan's "the verb's help epilog names the skill" is already done. The
  `__init__.py` touch may be a no-op, and r1 only checks it.
- The prototype's conclusion also says to report record-only units apart,
  because such a unit points at a choice made elsewhere. The plan counts any
  change that adds or amends a record as covered, so it drops that advice
  without saying why. The builder can fix this cheaply.
- For the dependency, not this plan: `_newest_decision_commit` takes the
  newest record file in the working tree. When that record is not committed
  yet (true in the decision-candidates worktree now, with ADR 0047 staged),
  `git log --diff-filter=A` finds nothing, so the default range becomes the
  whole history (165 changes there).
