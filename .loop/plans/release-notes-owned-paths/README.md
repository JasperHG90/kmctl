---
type: plan
title: 'Plan: release-notes-owned-paths'
description: kmctl's release notes leave out commits that touch only paths no package ships (.loop/, .okf/, .claude/, uv.lock), and release-tag's late-commit check uses the same rule from one place.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:20:24+00:00'
slug: release-notes-owned-paths
epic: monorepo-release
depends_on: []
priority: 3
schema_version: '2.0'
---

# release-notes-owned-paths

Relayed from: none

## Intent

`scripts/release_notes.py`'s `owns` gives kmctl `packages/kmctl/` and every
path outside `packages/`. That includes the repository's bookkeeping, which
ships in no package: the loop's state (`.loop/`), the knowledge bundle
(`.okf/`), the repository's own agent rules (`.claude/`) and the shared
`uv.lock`. A kmaudit ticket that also updates `.okf/` or the lock lands in
kmctl's notes. spike:release-notes-owned-paths/1 counted it: 7 of the 43
commits kmctl's notes kept over the last six releases touch nothing else,
and 5 of 17 in the coming release, among them the kmaudit-mcp and
kmaudit-briefing merges.

`owns` leaves those four out for both packages, so a commit that touches
only bookkeeping is in neither package's notes. A commit that touches
bookkeeping and a shipped path still counts for the package owning the
shipped path.

release-tag's late-commit step copies the rule in awk. The rule moves into
its own small script, `new:scripts/release_paths.py`: `owns(package, path)`
and a command that reads paths on stdin and exits 0 when the package owns
any of them. `release_notes.py` imports `owns` from it, and release-tag's
step pipes each late commit's paths to it instead of its awk, so the notes
and the warning cannot drift apart. release-tag still never runs
`release_notes.py`, so `test_release_tag_never_writes_its_own_notes` and
ADR 0012's "it no longer runs release_notes.py" stand unchanged: published
notes are never regenerated. The test gains one check, that the step calls
`release_paths.py` and holds no awk copy of the rule.

It worked when a commit touching only `.okf/` and `uv.lock` is in neither
package's notes nor in release-tag's late-commit warning, and a commit
touching `.okf/` and `packages/kmaudit/` is in kmaudit's.

## Problems

- P1: kmctl's release notes list commits that change only the repository's bookkeeping, so a kmaudit-only change shows up in kmctl's notes.

## Goals

- G1: Each package's notes list only commits that change what it ships.

## Outcomes

### O1: Bookkeeping paths belong to no package, in the notes and in release-tag's late-commit check alike
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:scripts/release_paths.py`, `scripts/release_notes.py`, `.github/workflows/release-tag.yml`, `tests/scripts/test_release_notes.py`, `tests/scripts/test_workflows.py`, `.okf/decisions/0012-releases-come-from-ci.md`
- checked by: release_notes tests that a commit touching only `.okf/` and `uv.lock` is in neither package's notes, one touching `.okf/` and `packages/kmaudit/` is in kmaudit's, and one touching `.claude/` and `docs/` is in kmctl's; release_paths.py tests over those path sets, as a function and as a command; a release-tag test that a late bookkeeping-only commit is not named and a late shipped one is; the workflow step calls `release_paths.py` with no awk copy of the rule, and still never names `release_notes.py`
- seen by: operator

## Could invalidate this plan

- Narrowing kmctl's paths could hide a change users need. spike:release-notes-owned-paths/1 lists the 7 commits it would have dropped: loop merges whose shipped paths are elsewhere, a prototype, a repository rule, an ADR and operator bookkeeping commits; none ships to kmctl users.
