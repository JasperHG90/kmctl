---
type: verdict
title: 'Verdict: plugin-install-known-marketplace plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of plugin-install-known-marketplace: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:31:19+00:00'
slug: plugin-install-known-marketplace
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach is right: claude accepts the add when the argument matches the
settings entry, and the spike shows that path ends with okf installed. But the
mapping from entry to argument is too coarse. Entries that pin a `ref` need
`#ref` on the argument (p1). Entries with fields the CLI cannot carry, such as
github `path`, have to be refused by kmctl itself, or the operator gets claude's
error again (p2). The managed settings sources are not named, and nothing shows
the operator's entry sits in one kmctl will read (p3). All three can be fixed by
revising the plan. None of them means rethinking it.

## Checked

- The spike /1 README, stdout and script. The git-URL case answers the main
  risk: the fixed add fails, the entry's URL add works, and the install gets okf.
- src/kmctl/plugin.py install(): OKF_SOURCE, the add, and the fallback to
  `marketplace update` for the kmctl add.
- My own probes against claude 2.1.300, with an isolated HOME, CLAUDE_CONFIG_DIR
  and XDG_DATA_HOME in the scratchpad (the real ~/.claude was not touched):
  - github with no ref, repo given: accepted.
  - github ref=main: repo refused, `repo#main` accepted.
  - github path=.claude-plugin/marketplace.json: repo refused.
  - git ref=main: url refused, `url#main` accepted.
  - url kind: the github repo refused, the entry's url accepted.
  - directory kind: the repo refused, the entry's path accepted.
  - A git entry placed in CLAUDE_CONFIG_DIR/settings.local.json: the repo add is
    accepted, so claude does not check settings.local.json at user level. The
    plan is right to read settings.json only.
  - Directory adds skip the check entirely: a directory add of scaccogatto or
    kmctl succeeds even when user settings declare that name from github or
    another folder. So the kmctl staged-folder add cannot hit this clash.
- The claude binary's strings name /etc/claude-code, /Library/Application
  Support/ClaudeCode, managed-settings.json, managed-settings.d/, and MDM.

## Findings

- p1: the github and git mapping drops `ref`, and claude refuses the add without
  it.
- p2: choosing pass or refuse by kind alone sends a github entry with `path` to
  claude, which refuses it, instead of to kmctl's PluginError.
- p3: the managed settings files are not named, managed-settings.d and MDM are
  not addressed, and nothing ties the fix to where the operator's entry lives.

## Notes

The `Could invalidate this plan` section says `none`. p1 and p2 were cheap to
find with the same isolated setup the spike used. Another direction to
consider: a directory add skips claude's check, but that would mean kmctl
cloning okf itself, which is outside this plan. I mention it only as context.
