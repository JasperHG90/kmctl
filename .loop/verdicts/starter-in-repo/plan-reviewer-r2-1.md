---
type: verdict
title: 'Verdict: starter-in-repo plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of starter-in-repo: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T10:04:14+00:00'
slug: starter-in-repo
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved. The plan now uses option 2: `just upgrade` stays
`copier update --defaults --data kmctl_ref=REF`, so the template moves to the
newest release and the pin goes to REF, older or newer. That is how
kmctl-starter already worked (its `upgrade` recipe at
template/justfile.jinja:50-51), so copier never has to downgrade and no tag
older than the template is ever asked for. r4 is gone, and r8 says the template
follows the newest release while kmctl_ref picks the CLI and package. I found
no new risk that could break the plan.

## Checked

- The kmctl_ref validator in /home/vscode/kmctl-starter/copier.yml. Widening
  the regex to allow a, b or rc is enough. The OpenCode floor check runs
  `int` on each part, and Jinja's `int` filter turns "0rc1" into 0 instead of
  raising, so v0.6.0rc1 compares as [0, 6, 0] and passes. r3 covers this.
- Render tests with `--vcs-ref HEAD` avoid the newest-tag problem from round 1
  (v0.5.1 has no template, and CI's shallow checkout has no tags).
- Spikes 1, 2, 4 and 5 still settle the three listed risks, as round 1 found.
  Nothing in the revision changes what they cover.

## Findings

- p1: resolved. just upgrade keeps no --vcs-ref, the template follows the newest release, and r8 says so.

## Notes

- If a gate runs in a worktree where starter/ is not committed yet, copier
  copies the uncommitted tree for `--vcs-ref HEAD` and raises
  DirtyLocalWarning. If pytest turns warnings into errors, filter that one
  warning in the test. The first run will show it.
- No split is needed.
