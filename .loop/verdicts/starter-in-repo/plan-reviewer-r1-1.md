---
type: verdict
title: 'Verdict: starter-in-repo plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of starter-in-repo: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T10:02:40+00:00'
slug: starter-in-repo
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds. Spikes 1, 2 and 5 settle the three listed risks with evidence
that matches their claims. The release path also works: the version pull request
carries copier.yml's default and release-tag.yml tags that merge commit, and copier
skips pre-release tags by default. One design gap needs a decision before building.
The plan says the template and the pin are one tag, but its validator and the new
upgrade recipe do not agree with that for refs older than the template or older than
the project's current tag (p1). The verdict is fail, so the plan gets a revision and
a second look, not a rethink.

## Checked

- Spike 1 (README, stdout, run.json, exit 0). With copier 9.19.1, a root copier.yml
  with `_subdirectory: starter` renders from the newest tag of a kmctl clone whose
  older tags have no copier.yml, and none of kmctl's root files leak in. Settles risk 1
  for a local source. The gh: source is checked after the release, as the plan's
  last step says.
- Spike 5 (exit 0). uv tool install, uvx --from and APM 0.33.0 apm install all
  follow a file:// insteadOf rewrite, and the lock records the served commit. Spike 4
  shows APM refuses an http:// rewrite. Settles risk 2. The plan's integration test
  uses file://, not the http `served` fixture in tests/conftest.py. That is a new
  fixture variant, which is fine.
- Spike 2 (exit 0). recopy after the `_src_path` edit keeps the answers and moves
  `_commit` to the new tag. A later update works. Plain update leaves conflicts.
  Settles risk 3, and the how-to says to use recopy.
- Release flow. scripts/release.py set_version returns the files it wrote, and the
  bump step's `git diff --exit-code` check catches any file it forgot to stage.
  tests/scripts/test_workflows.py:110-130 compares the staged set against the files
  written, so adding copier.yml to both is consistent. release-tag.yml runs on
  apm/apm.yml, which the same pull request changes. The release workflow's test job
  runs plain pytest, so r2 (default == v<apm version>) holds before the bump
  (v0.5.1/0.5.1) and after it (v0.6.0/0.6.0).
- Pre-release tags. copier skips pre-release tags unless --prereleases is given, so a
  default of v0.6.0rc1 on main does not change what `copier copy` picks. The first
  template release is a final MINOR (v0.6.0), so copier never picks v0.5.1, which
  has no template.
- CI and privacy. kmctl and kmctl-starter are both private (gh repo view). In the
  starter job, only okf-skills (public) and PyPI are fetched from outside, and
  spike 5 needed no token. ci.yml's tests job runs `not integration`, so the render
  tests need copier in the dev group, which the plan adds.
- prek workspaces. I ran prek 0.5.5 on a repo with a nested config: it does run a
  nested .pre-commit-config.yaml. So starter/.pre-commit-config.yaml becomes part of
  kmctl's own prek run, in CI and in the hook. I ran it on kmctl-starter's template
  files under starter/ and every hook passes, so this does not break anything.
- copier downgrade refusal: copier/_main.py:1381 in the cached copier package.

## Findings

- p1: the plan's "one tag" model conflicts with a validator that accepts pins older
  than the template, and with copier's downgrade refusal under `just upgrade
  --vcs-ref`. It needs a decision on the floor and on which way upgrade can move,
  carried into r3, r4 and r8.

## Notes

- When copier renders from a local git path with no --vcs-ref, it uses the newest
  tag, not the working tree. In the primary checkout today that is v0.5.1, which has
  no copier.yml. After the release it is v0.6.0, which would hide working-tree
  changes. CI's shallow checkout has no tags. So the render tests should pass
  --vcs-ref HEAD, or render from the file:// clone the bootstrap test builds. A build
  finds this on the first run.
- The post-landing steps (dispatching a real release, merging its pull request,
  archiving JasperHG90/kmctl-starter) are outward actions done unattended. They are
  within what the operator asked for, and archiving can be undone.
- The plan does not need to be split. The listed risks are settled, and p1 is one
  decision.
