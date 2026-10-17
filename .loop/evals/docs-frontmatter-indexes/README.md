---
type: eval
title: 'Eval: docs-frontmatter-indexes'
description: 'Definition of done for docs-frontmatter-indexes: 13 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T16:46:41+00:00'
slug: docs-frontmatter-indexes
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: 0b5844e8868aaac71b2af73ba349ffda1ad5e8f424d8004e52a9f82e5914ae90
  at: '2026-10-17T16:46:41+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl check --fix writes each Diataxis folder's README.md from its pages: a marker comment saying kmctl writes it, then one entry per page with its H1 title as link text and its description front matter when present; it changes no other file, and a second run changes nothing.
  Fails when: a page is missing or extra, an entry lacks the title or the description a page has, the marker is missing, --fix changes the root index, .okf/ or any other file, or a second run changes a file
- r2: kmctl check fails (exit 1) with exactly one error when a Diataxis folder has no README.md or its index differs from what kmctl would generate, with a fix naming kmctl check --fix; a page directly in docs/ or outside the four folders that docs/README.md does not list is still an error.
  Fails when: check exits 0, reports other than one error for either folder case, the fix does not name kmctl check --fix, or an unlisted page outside the four folders passes
- r3: When docs/README.md has no link to a folder index, kmctl check reports one finding at the new warning level and exits 0, and the CI action's summary shows the warning and the action passes.
  Fails when: check exits nonzero, reports it as an error or not at all, or the action fails or omits the warning
- r4: A folder README.md without kmctl's marker is never overwritten by kmctl check --fix, kmctl new doc or kmctl update, and kmctl check warns (exit 0) that kmctl does not manage it.
  Fails when: any of the three changes the hand-written file, or check errors or says nothing
- r5: kmctl new doc writes description (from --description), stale_after three months ahead and an empty sources, never verified, and regenerates its folder index; kmctl update writes each missing folder index and leaves an existing docs/README.md unchanged.
  Fails when: a field is missing or wrong, verified is written, the folder index lacks the new page, or update changes docs/README.md or skips a missing folder index
- r6: kmctl review due lists a docs page whose stale_after has passed, or one of whose listed sources was committed after the page's latest verified date or, with none, after the page's own last commit, with an id starting docs/ and the same --json shape, also in a repo with no .okf/; a docs page with no verified, or with no front matter, is not listed for that alone.
  Fails when: a stale or source-changed docs page is missing, a page is listed when no source changed since its baseline, its id lacks the docs/ prefix, the --json shape changes, docs pages are skipped without .okf/, or a page is due only for a missing verified
- r7: kmctl check reports an error for a docs page whose description, stale_after, verified or sources has the wrong shape, naming the page and the field; a page with no front matter passes.
  Fails when: a malformed field passes, the finding omits the page or field, or a page with no front matter fails
- r8: This repo's docs/ is migrated: four generated folder indexes, docs/README.md links each folder, every page carries a description, and kmctl check on the repo passes with no warnings; docs/ holds no okf_version, log.md or type field.
  Fails when: check reports an error or warning on the repo, a page lacks a description, or docs/ carries an OKF bundle marker
- r9: A new decision records docs front matter, generated indexes and the pre-commit hook and amends ADR 0006; the manifesto's I4 names the docs fields and its kmctl description names kmctl check --fix; this repo's .claude/rules/docs-layout.md, docs/reference/commands.md (check --fix and the warning level) and the briefing line match.
  Fails when: the decision is missing or does not amend ADR 0006, or any of those pages still describes the flat index or omits the front matter or check --fix
- r11: .pre-commit-hooks.yaml offers hook kmctl-check, which runs kmctl check without passing file names (checked offline); and, as an integration test, prek in a scratch repo listing a temporary commit of this checkout under repos: fails kmctl-check on a missing folder index, writes it with args: [--fix], and passes on a second run.
  Fails when: the hook id is missing, it passes file names, the integration test selects no test, the hook passes with a missing folder index, or --fix does not write it
- r12: This repo's .pre-commit-config.yaml runs kmctl-check.
  Fails when: no hook in the config runs kmctl check
- r13: The agent instructions kmctl ships say docs pages may carry description, stale_after, verified and sources, that folder indexes are generated, and to run kmctl check --fix rather than edit one: the docs-layout rule and its Antigravity copy, the CLAUDE.md/AGENTS.md block kmctl init writes, the write-docs skill, the auditor agent and the audit skill.
  Fails when: any of them still says to edit an index by hand, describes only the flat docs/README.md index, or omits the front matter or kmctl check --fix
- r10 (judgment): The decision and the changed pages say in plain language why docs/ borrows OKF fields without becoming a bundle, and why folder indexes are generated while the root index stays hand-written.
  Fails when: the reasoning is missing, contradicts the plan, or reads as jargon
