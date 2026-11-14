---
type: plan
title: 'Plan: kmaudit-namespaces'
description: kmaudit audits any folder of markdown docs, each folder in its own store, listed by kmaudit namespaces.
tags:
- plan
generated: {by: 'process:loopctl/2.3.1.dev65+g93b143856', at: '2026-11-14T13:03:43+00:00'}
slug: kmaudit-namespaces
epic: kmaudit
depends_on:
- kmaudit-package
priority: 1
schema_version: '2.0'
---

# kmaudit-namespaces

Relayed from: kmaudit-package-reviewer-f2, PREVIOUS_HASHES must be emptied whenever GUIDANCE changes, and nothing says so or fails when it is not

## Intent

The operator wants kmaudit to work on any folder of markdown docs the user
points it at (`docs/`, `.okf/` or another), each folder in its own
namespace so two never clash. Today `resolve_target` in
`packages/kmaudit/src/kmaudit/sections.py` accepts only an OKF bundle or a
repository holding `.okf/`, and every verb opens the one store at
.kmctl/audit.sqlite through `Store(target.root)` (16 call sites). The
other places that assume `.okf/` are the folders checks never read
(`EXCLUDE_DIRS` in `packages/kmaudit/src/kmaudit/steps.py`) and the CLI help.

After this ticket, a verb's path names a folder of markdown (or one file in
it). The namespace is that folder's path relative to the repository root
(`.okf`, `docs`, `handbook/guides`), and its store is one SQLite file under
`.kmaudit/` at the repository root, which ignores itself in git, so two
folders never share a section, claim or check. An OKF bundle keeps today's
rules (its `index.md`, `log.md` and `prototypes/` are skipped, deprecated
concepts left out); any other folder audits every `.md` file in it. Checks
never read the audited folder: `Repository` in `steps.py` takes it, so
checks, coverage and the review page's code view leave it out (12 call
sites in `check_verbs.py`, `ui.py` and `coverage.py`). The page shows each
page's real path instead of .okf/CONCEPT.md, and the check writer's
instructions say the audited folder is never read. The repository root holding `.okf/` still
means `.okf`, as today. `kmaudit namespaces` lists the namespaces with their
folder and counts. A repository with the old .kmctl/audit.sqlite gets it
copied into the `.okf` namespace the first time that namespace opens, so no
answer is lost; the old file is left alone.

Measured before the plan: the current cutter reads this repository's
`docs/` (13 pages, not an OKF bundle) into 89 sections with no failure, and
this repository's store holds 207 sections, 1281 claims and 1137 checks
that must survive the move.

The relayed finding: `PREVIOUS_HASHES` in
`packages/kmaudit/src/kmaudit/instructions.py` carries answers across only
while `GUIDANCE` is unchanged; a comment on `GUIDANCE` says so and a test
pins the guidance hash, failing with the instruction to empty the tuple.

It worked when `kmaudit claims todo docs` and `kmaudit claims todo .okf` in
one repository hand out their own sections from two stores, and the copied
store hands out nothing for `.okf`.

## Problems

- P1: kmaudit refuses any folder that is not an OKF bundle, so docs in another layout cannot be audited.
- P2: Every folder would share one store, so two audited folders would clash.
- P3: Nobody can see which folders have been audited.
- P4: A repository's existing audit store would be orphaned by a new store location.
- P5: Nothing stops a later guidance change from carrying old answers over through PREVIOUS_HASHES.

## Goals

- G1: Any folder of markdown docs can be audited, each on its own.
- G2: Work already done is kept.

## Outcomes

### O1: Any folder of markdown docs is a namespace with its own store
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmaudit/src/kmaudit/sections.py`, `packages/kmaudit/src/kmaudit/steps.py`, `packages/kmaudit/src/kmaudit/cli.py`, `packages/kmaudit/src/kmaudit/check_instructions.py`, `packages/kmaudit/src/kmaudit/ui.html`, `new:packages/kmaudit/tests/test_namespaces.py`
- checked by: a test that `kmaudit claims todo docs` in a fixture repository with a plain `docs/` folder hands out its sections, skips nothing in it, and that a check never reads a file in the audited folder
- seen by: operator

### O2: Each namespace keeps its own store under .kmaudit/
- kind: support
- goal: G1
- fixes: P2
- needs: O1
- touches: `packages/kmaudit/src/kmaudit/store.py`, `packages/kmaudit/src/kmaudit/verbs.py`, `packages/kmaudit/src/kmaudit/check_verbs.py`, `packages/kmaudit/src/kmaudit/ui.py`, `packages/kmaudit/src/kmaudit/coverage.py`
- checked by: a test that claims submitted for `docs` never show in `kmaudit claims list .okf` and the reverse, with two store files under `.kmaudit/`
- seen by: calling code

### O3: kmaudit namespaces lists each namespace, its folder and counts
- kind: behaviour
- goal: G1
- fixes: P3
- needs: O2
- touches: `packages/kmaudit/src/kmaudit/cli.py`, `packages/kmaudit/docs/commands.md`
- checked by: a test that `kmaudit namespaces --json` lists both namespaces with folder, sections, claims and checks
- seen by: operator

### O4: The old .kmctl/audit.sqlite is copied into the .okf namespace
- kind: support
- goal: G2
- fixes: P4
- needs: O2
- touches: `packages/kmaudit/src/kmaudit/store.py`
- checked by: a test that a repository with only .kmctl/audit.sqlite opens `.okf` with every row of every table, and the old file unchanged; and a run on a copy of this repository's store hands out 0 sections for `.okf`
- seen by: operator

### O5: A guidance change cannot carry old answers over silently
- kind: support
- goal: G2
- fixes: P5
- needs: none
- touches: `packages/kmaudit/src/kmaudit/instructions.py`, `packages/kmaudit/tests/test_claims_sections.py`
- checked by: a test pinning `instructions_hash()`, whose failure message says to empty PREVIOUS_HASHES
- seen by: nobody

## Could invalidate this plan

- A plain folder may hit `.okf/` assumptions outside this plan's touched
  files, so it would audit but some verb, the page or the line windows
  would break, widening the ticket. spike:kmaudit-namespaces/1 ran every
  verb on a plain folder (as `docs/` and `handbook/`): none raised, the
  page lists its pages, line windows work without `sources`, and the sites
  it found (`SKIP_NAMES`, `Repository` knowing only the root, the page's
  hard-coded `.okf/` path, the check instructions' folder list) are now in
  the touches above. spike:kmaudit-namespaces/2 reruns it against the
  widened touches and finds nothing outside them.
