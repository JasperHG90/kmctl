---
type: eval
title: 'Eval: docs-frontmatter-indexes'
description: 'Definition of done for docs-frontmatter-indexes: 10 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T16:38:37+00:00'
slug: docs-frontmatter-indexes
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: f09283d3ded0a298e1753488d3625838409308a71e9c0c02031c66e35ff40388
  at: '2026-10-17T16:38:37+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl docs index writes each Diataxis folder's README.md from its pages: a marker comment saying kmctl writes it, then one entry per page with its H1 title as link text and its description front matter when present; a second run changes nothing.
  Fails when: a page is missing or extra, an entry lacks the title or the description a page has, the marker is missing, or a second run changes a file
- r2: kmctl check fails (exit 1) with exactly one error when a folder index differs from what kmctl would generate, and its fix names kmctl docs index.
  Fails when: check exits 0, reports other than one error, or the fix does not name kmctl docs index
- r3: When docs/README.md has no link to a folder index, kmctl check reports one finding at the new warning level and exits 0, and the CI action's summary shows the warning and the action passes.
  Fails when: check exits nonzero, reports it as an error or not at all, or the action fails or omits the warning
- r4: A folder README.md without kmctl's marker is never overwritten by kmctl docs index, kmctl new doc or kmctl update, and kmctl check warns (exit 0) that kmctl does not manage it.
  Fails when: any of the three changes the hand-written file, or check errors or says nothing
- r5: kmctl new doc writes description (from --description), stale_after three months ahead and an empty sources, never verified, and regenerates its folder index; kmctl update writes each missing folder index and leaves an existing docs/README.md unchanged.
  Fails when: a field is missing or wrong, verified is written, the folder index lacks the new page, or update changes docs/README.md or skips a missing folder index
- r6: kmctl review due lists a docs page whose stale_after has passed or whose listed source changed, with an id starting docs/ and the same --json shape; a docs page with no verified, or with no front matter, is not listed for that.
  Fails when: a stale or source-changed docs page is missing, its id lacks the docs/ prefix, the --json shape changes, or a page is due only for a missing verified
- r7: kmctl check reports an error for a docs page whose description, stale_after, verified or sources has the wrong shape, naming the page and the field; a page with no front matter passes.
  Fails when: a malformed field passes, the finding omits the page or field, or a page with no front matter fails
- r8: This repo's docs/ is migrated: four generated folder indexes, docs/README.md links each folder, every page carries a description, and kmctl check on the repo passes with no warnings; docs/ holds no okf_version, log.md or type field.
  Fails when: check reports an error or warning on the repo, a page lacks a description, or docs/ carries an OKF bundle marker
- r9: A new decision records docs front matter and generated indexes and amends ADR 0006; the manifesto's I4 names the docs fields and its kmctl description names kmctl docs index; docs-layout.md, docs/reference/commands.md (kmctl docs index and the warning level), the write-docs skill and the briefing line match.
  Fails when: the decision is missing or does not amend ADR 0006, or any of those pages still describes the flat index or omits the front matter or kmctl docs index
- r10 (judgment): The decision and the changed pages say in plain language why docs/ borrows OKF fields without becoming a bundle, and why folder indexes are generated while the root index stays hand-written.
  Fails when: the reasoning is missing, contradicts the plan, or reads as jargon
