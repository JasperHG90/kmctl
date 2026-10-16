---
type: verdict
title: 'Verdict: apm-only-install-reviewer-f2 plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of apm-only-install-reviewer-f2: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T22:21:17+00:00'
slug: apm-only-install-reviewer-f2
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 risks are settled in the plan, and I found no new risk that could break it. The lock-side URL is now built from host, port and repo_url, which matches what APM 0.33.0 writes. The reverse order no longer reaches apm uninstall, because kmctl's own mapping form drops out of `_names_old_package`.

## Checked

- spike:apm-only-install/4 and /5 stdout.txt: the lock records `repo_url: o/pkg`, `host: 127.0.0.1`, `port: N` for a local git source. Built as `host:port/repo_url`, that gives `127.0.0.1:N/o/kmctl`. The plan's normalised entry URL for `http://127.0.0.1:N/o/kmctl.git` gives the same, so the local-source-then-default case matches. Round 1 found that spike 6 locks the kmctl entry with virtual_path apm, so the plan's `name: kmctl`, `virtual_path: apm` test holds.
- src/kmctl/plugin.py: `_names_old_package`, `_is_kmctl_entry`, `remove_old_apm_entry`, `write_manifest`, `read_lock` (scope-aware), `kmctl_package` and install's order. With `_names_old_package` limited to the string form (and mappings without `path: apm`), a `{git: DEFAULT_SOURCE, path: apm}` entry is not uninstalled when the source changes. `write_manifest` then catches it by the knowledge-management name rule and replaces it in place.
- Default-source entries never rely on the lock, because the name rule catches them. So a default lock without a `port` field is not a problem.
- No regression for a hand-written ADR 0013 mapping at the default URL: today `_is_kmctl_entry` already keeps that entry out of uninstall when the source is the default, so the plan does not change what happens to it.
- Eval rows r1 and r2 cover both orders, the no-uninstall check, the real lock shape and the unrelated `path: apm` package.

## Findings

- p1: resolved. The plan adds host and port to LockDependency and compares `host[:port]/repo_url` with the normalised entry URL. The spike lock files back this up.
- p2: resolved. `_names_old_package` no longer matches kmctl's own mapping form, so the reverse order skips apm uninstall. r1 tests this.

## Notes

The phrase "a mapping without `path: apm`" in the `_names_old_package` change widens the match to mappings that name knowledge-management under some other path. Today no mapping without `path: apm` matches at all. For such an entry, `apm uninstall` of the old package would probably leave it in place, and install would then stop with the "left the entry" error. ADR 0013 only told users to write the string form, so this is unlikely to come up. The builder should decide whether the mapping case is needed at all. It is not a risk to the plan.
