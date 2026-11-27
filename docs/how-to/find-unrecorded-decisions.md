---
description: "Ask your agent which changes in your git history made a decision with no record, read its report, and record the ones you choose."
stale_after: 2027-02-16
sources:
  - resource: "packages/kmctl/apm/.apm/skills/decision-gaps/SKILL.md"
  - resource: "packages/kmctl/src/kmctl/candidates.py"
verified:
  - by: human:jasper
    at: 2026-11-27T20:44:03Z
---

# Find unrecorded decisions

Changes sometimes commit a project to one option over another without
anyone writing a decision record. kmctl's `decision-gaps` skill finds those
changes in your git history and reports them. It writes nothing: you read
the report and decide which findings become records.

## Before you start

- kmctl's APM package is installed in the repository, so your agent has the
  `decision-gaps` skill ([Install kmctl with APM](install-kmctl-with-apm.md)).
- The `kmctl` CLI on your PATH is the same release, since the skill runs
  `kmctl decision candidates`.

## Steps

1. Ask your agent, in your own words. For example:

   > Which decisions did we make since v0.13.0 that never got a record?

   With no starting point, it looks at the changes since the newest
   committed decision record. Name a tag, a sha or a release to look
   further back.

2. If the range is long (more than about forty changes), the agent says
   how many there are and asks whether to go ahead or narrow it. Each
   change costs a few seconds and a little context to judge.

3. Read the report. It lists each change that made a decision no record
   covers, with the choice, the option it turned down and the change it
   came from; then the changes that only added a record; then how many
   changes it judged, found covered and found not to be decisions.

4. For each finding you want to keep, write the record yourself or ask the
   agent to draft it:

   ```
   kmctl new decision "License kmctl under MIT" --description "One sentence on the choice."
   ```

   Treat each finding as a lead to confirm: measured on kmctl's own history,
   about six in ten of its claims were real gaps
   ([ADR 0047](../../.okf/decisions/0047-unrecorded-decisions-are-listed-by-kmctl-and-judged-by-a-skill-that-only-reports.md)).

## Check it worked

`git status` shows no change under `.okf/` after the report: the skill
writes nothing. Run `kmctl decision candidates` yourself to see the list of
changes the agent judged.
