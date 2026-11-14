---
type: plan
title: 'Plan: release-notes-hermes'
description: The manual Release run has Hermes rewrite the deterministic notes draft into user-facing notes, and a cleaning script keeps the rewrite only when it passes checks, else the draft stands.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:21:08+00:00'
slug: release-notes-hermes
epic: monorepo-release
depends_on:
- release-per-package
priority: null
schema_version: '2.0'
---

# release-notes-hermes

Relayed from: none

## Intent

Part of epic `monorepo-release`, under the operator's ask: "How can we ensure
proper release notes automatically? Use the hermes issue triage setup? Would
be good." This ticket is D3's Hermes half. `release-per-package` (which this
depends on) gives the manual Release run (`.github/workflows/release.yml`) a
`package: kmctl|kmaudit` input, runs `scripts/release_notes.py` for that
package to write a deterministic draft, commits it as the notes file in the
version pull request and puts it in the pull request body. This ticket puts
one step between the draft and that file.

After the draft is written, the run calls the same Hermes action as
`.github/workflows/hermes-issue-triage.yaml` (`JasperHG90/toiminnot/actions/hermes`
at the same SHA pin, `secrets.OLLAMA_API_KEY`, model `deepseek-v4.1-flash`)
with a new system prompt, `new:.github/prompts/release-notes-system.md`, and
the draft as the user message. The prompt asks Hermes to rewrite the What
changed bullets into short, user-facing lines (what a user can now do or what
broke and is fixed), keep each bullet's `` (`slug`) `` or `(#N)` reference, and
leave every other section as written. A new cleaning script,
`new:scripts/hermes_release_notes.py`, built the way `scripts/hermes_triage.py`
is (ADR 0035), takes the draft and Hermes' response file and prints the notes
the run commits. It keeps the rewrite only when all of these hold, and
otherwise prints the draft unchanged with a `::warning::` that names the
failed check:

- the response file exists and is non-empty once cleaned;
- cleaning strips HTML comments and trailers, any preamble before the first
  `## ` heading, and a code fence wrapped round the whole response;
- the `## ` headings are the draft's, in the draft's order;
- everything from `## Other changes` to the end (the other changes, the
  install lines and the compare link or "First release.") matches the draft,
  ignoring trailing whitespace, so the rewrite touches only What changed;
- under What changed, the set of references (`` (`slug`) `` and `(#N)`) equals
  the draft's: no change the draft lacks, none dropped, and each bullet
  carries at least one.

The script compares against the draft, not the template, so it works for
whichever template `release-per-package` gives each package. The script never
fails the run: a missing response file, a Hermes step that errors
(`continue-on-error: true`, with a timeout) or a rejected rewrite all end in
the draft, so D3's rule holds: when Hermes fails or returns nothing, the
deterministic draft stands. The step runs in dry runs too, and the run writes
the chosen notes and which source won (Hermes or draft) to the step summary,
so a dry run previews the notes before the real run opens the pull request.

Choices made here that the operator may reverse:

- Hermes rewrites only What changed. Other changes (raw commit subjects) and
  the install lines stay as the draft wrote them; a person edits them in the
  pull request if needed. This keeps the fabrication check mechanical.
- The reference rule refuses dropped changes as well as added ones, because
  `.claude/rules/releases.md` treats notes that leave out a change as a bug.

Decisions already made for the epic (from the shared brief, not reopened):
D1 kmctl moves to `packages/kmctl`; D2 kmctl keeps `vX.Y.Z` tags and kmaudit
gets `kmaudit-vX.Y.Z`, each package's notes covering only commits that touch
its paths; D3 the Release run writes the notes into the version pull request
as a file, Hermes rewrites them, the draft stands when Hermes fails, merging
approves the notes, and release-tag refuses to publish a missing or empty
file; D4 the CI workflow is `CI` with per-package jobs; D5 a repo-local
release skill at .claude/skills/release/SKILL.md.

The ADR 0035 record gains this third Hermes use in
`.okf/decisions/0035-kmctl-s-repository-answers-and-triages-with-hermes.md`
(its decision list, sources and consequences: commit subjects from main reach
Hermes with the key, as issue bodies do).

Outcome that shows it worked: `tests/scripts/test_workflows.py` pins the
Hermes step (SHA, secret, model, prompt path, `continue-on-error`) between the
draft and the notes file in `release.yml`, and
`new:tests/scripts/test_hermes_release_notes.py` shows that a good rewrite is
kept and that each failure (missing file, empty response, a heading lost, the
compare link changed, a reference added, a reference dropped) yields the draft
byte for byte.

## Problems

- P1: The Release run's notes are the deterministic draft: bare ticket summaries and commit subjects written for the loop, not for users
- P2: Nothing checks a model's rewrite of release notes, so a Hermes reply could drop the compare link, invent a change or leave out a real one

## Goals

- G1: Each release's notes in the version pull request read as user-facing prose without a human writing them
- G2: The notes never list a change the release lacks or miss one it holds, and a Hermes failure never blocks a release or empties its notes

## Outcomes

### O1: A cleaning script keeps Hermes' rewrite only when it passes the checks, else prints the draft
- kind: support
- goal: G2
- fixes: P2
- needs: none
- touches: `new:scripts/hermes_release_notes.py`, `new:tests/scripts/test_hermes_release_notes.py`
- checked by: `tests/scripts/test_hermes_release_notes.py`, one test per check plus a kept rewrite
- seen by: nobody

### O2: The Release run rewrites the draft with Hermes and commits the checked result as the notes file
- kind: behaviour
- goal: G1
- fixes: P1
- needs: O1
- touches: `.github/workflows/release.yml`, `new:.github/prompts/release-notes-system.md`, `tests/scripts/test_workflows.py`, `.okf/decisions/0035-kmctl-s-repository-answers-and-triages-with-hermes.md`
- checked by: workflow tests pinning the Hermes step's SHA, secret, model, prompt and continue-on-error, and that the notes file comes from the cleaning script's output
- seen by: operator

## Could invalidate this plan

- The reference rule may be too strict for the model: if `deepseek-v4.1-flash`, given the new prompt and a real draft, usually merges, drops or rewords the `` (`slug`) ``/`(#N)` references or touches the sections it must leave alone, the script falls back almost every time and the Hermes step adds cost and nothing else; the checks or the scope of the rewrite would have to change. spike:release-notes-hermes/1 measured it through Bifrost (`ollama/deepseek-v4.1-flash`, one chat call per draft with a draft of the new prompt): 15 of 15 rewrites of five real drafts (v0.9.0 to v0.12.1, three runs each) kept every check, and the rewrites were real rewordings, not copies. The checks do not catch vague wording, which the person merging the pull request still reads for.
