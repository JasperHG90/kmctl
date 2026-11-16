---
type: verdict
title: 'Verdict: decision-gaps-skill reviewer round 1'
description: 'reviewer verdict for round 1 of decision-gaps-skill: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T18:08:48+00:00'
slug: decision-gaps-skill
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The skill does what the plan and ADR 0047 ask. It runs `kmctl decision candidates`, judges every change in batches of about ten against one shared reference, and asks before judging more than about forty. It reports missing decisions with the choice, the rejected option and the change, lists record-only changes on their own, and writes nothing to the repository. It follows each build point in the prototype's conclusion. The gates and all three eval rows pass. results.md reports the runs honestly, including the weak triggering. Two non-blocking fixes: results.md says something false about the briefing (f1), and judging.md lets covered and record-only overlap (f2).

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2 and r3 all pass; "stamp green: a65aefefc9904cf358c58727b63e48f1cb19b012c594517fa5d39523034357b7". I also ran the r2 and r3 commands and `kmctl check` ("all checks passed") myself.
- Read SKILL.md, references/judging.md, the three case folders, results.md, trigger-queries.json, the new test file and the docs, README and .okf diffs in full. Checked them against ADR 0047 and the prototype's Conclusion: judge every unit, show the unit's own record changes (`recorded` counts as covered), give it the plan intent and the decision index as it stood before, treat features and interface details as not decisions, and report record-only changes apart. All are present. `kmctl decision candidates --help` and `--json` match the fields and table columns SKILL.md describes.
- Eval rows. r1: test_decision_gaps_skill checks front matter, every body instruction (verb, --json, judge every change, batches, subagent, the forty limit, the record-only section, writes nothing, kmctl new decision, Instead of) and the eight-skill install pages. test_apm_package's SKILL_NAMES and wheel test cover the package and wheel, and test_briefing_names_every_skill reads the skills folder, so the briefing row holds without editing test_briefing.py. r2: the case-folder format, the three cases, the named range against no range, the write case's "did not run" grader, and results.md's per-case sections, label counts and .okf/ status are all asserted. r3: the page's "It writes nothing" and "you decide" text and the index entry are asserted, and test_this_repo_docs_are_migrated runs the checks. Each test fails when its row's fails_when holds.
- Spot-checked the skill-creator workspace. Grading.json for iteration-1 (all six runs) and iteration-3 (runs 1 and 2 at 7/7, baseline at 5/7) match results.md's tables. Iteration-2's with-skill runs have no grading.json. I read those reports against the graders, and the 5-of-7 (collector job dropped, a4c175d9 listed as missing) and 4-of-4 grades hold. The labels for 2cf55821c..dd1158d3 give four gap claims (ce8b712c, da6a34c5, 09af291c, c92c6e0d) and one false_alarm (642d7236), as results.md says. Every run's clone sits at 3ed985ef, which adds only loop commits after dd1158d3. Each read-only run's clone is clean, and only the write case's clones hold a new ADR 0048. trigger-results.json (2 of 8 should-trigger queries, each 1 of 3 runs, no near misses) and loop-log.txt (held-out recall 11% then 22%, best is the original description) match results.md.

## Findings

- f1 (docs, non-blocking): `briefing._skill_summary` keeps the description's first sentence cut at 12 words. So `kmctl briefing` prints "decision-gaps: Find the changes in a repository's git history that made a decision..." and never shows when to use the skill. Correct results.md's last paragraph. Better still, open the description with a whole first sentence of 12 words or fewer (for example "Find the changes in git history that made a decision no record covers."), so the briefing line, the only cue that helps triggering, reads whole.
- f2 (design, non-blocking): in judging.md, state that a change whose files are all under `.okf/` or `.loop/` and that adds a record is record-only even though `recorded` is set, or move the record-only rule ahead of covered. The test needle "**covered**: `recorded` is not empty" will need changing with it.

## Notes

- Triggering misses the plan's "It worked when" clause about the description triggering on asks to find unrecorded decisions: recall from the description alone is 2 of 8 in `run_eval` and 11 to 22% held out. results.md says so plainly, and `run_loop` found nothing better, so this is for the operator to weigh, not a fault in the change. The briefing line (see f1) and `/decision-gaps` are the practical routes in.
- The final skill (round 3, with references/judging.md) ran only on the known-range case. The default-range and write cases last ran on rounds 1 and 2. The results tables show this by round, so the report is accurate.
