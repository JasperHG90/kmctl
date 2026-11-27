---
description: "Have your agent list the draft decision records on your branch, say yes or no to each, and mark the pull request ready once none is left."
stale_after: 2027-02-23
sources:
  - resource: "packages/kmctl/src/kmctl/accept.py"
  - resource: "packages/kmctl/src/kmctl/checks.py"
  - resource: "action/knowledge-ci.sh"
verified:
  - by: human:jasper
    at: 2026-11-27T20:44:03Z
---

# Accept or drop draft decisions before review

Your coding agent writes a decision record as a draft
(`kmctl new decision --draft`) when it records a choice for you. A draft is
fine while the pull request is a draft too. Before review, you say yes or
no to each one, and the agent runs the command. kmctl's CI action fails a
pull request that is ready for review while a draft is left.

## Before you start

- kmctl's APM package is installed, so your agent has the knowledge rules
  that tell it to list drafts before review
  ([Install kmctl with APM](install-kmctl-with-apm.md)).
- The repository's CI runs kmctl's action in `checks` mode, with
  `ready_for_review` in its `pull_request` types
  ([Install the plugin and the CI action](install-the-plugin-and-the-ci-action.md)).

## Steps

1. Before you mark the pull request ready, ask your agent, in your own
   words. For example:

   > Which draft decisions are on this branch?

   It runs `kmctl check --no-drafts` and explains each draft in a sentence
   or two: the choice and the option it turned down.

2. Answer for each draft: accept, change or drop.

   - **Accept.** The agent runs
     `kmctl decision accept 12 --by human:<your id>`. The record's `status`
     becomes `stable`, and `.okf/log.md` gets a line with your id.
   - **Change.** Tell the agent what to change. It edits the record, and
     you answer again.
   - **Drop.** The agent deletes the record's file and its line in
     `.okf/decisions/index.md`.

   The agent never accepts a draft you did not say yes to.

3. Push, then mark the pull request ready for review.

## Check it worked

- `kmctl check --no-drafts` prints `all checks passed`.
- On the pull request, the knowledge job passes. Its summary starts with
  `Draft decisions fail (drafts: fail-when-ready).`, which means it checked
  for drafts.

If the job fails with `error  draft`, a draft is left: go back to step 1.
If your repository has drafts from before it used this check, the first
ready pull request lists them all; accept or drop each once.
