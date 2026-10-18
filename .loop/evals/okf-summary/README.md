---
type: eval
title: 'Eval: okf-summary'
description: 'Definition of done for okf-summary: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T20:00:49+00:00'
slug: okf-summary
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: bc7b66b6eb6fee786eb59c1abbdc3ebae2fc95ab86d907e8fd5ab28a8fb39d07
  at: '2026-10-18T20:00:49+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init writes .okf/summary.md with type: summary and the sections Decisions, Architecture, Open work, Practices and Known gaps, links it from .okf/index.md, and the bundle passes strict OKF validation; kmctl schema summary prints the kind's schema; kmctl new does not offer summary as a concept to add (there is one).
  Fails when: the file, a section or the index link is missing, strict validation fails, or kmctl schema summary fails
- r2: kmctl check fails when the summary's body (outside front matter) is over 500 words, naming the count and the limit, and passes at 500 words or fewer.
  Fails when: a 501-word body passes, a 500-word body fails, or the failure does not name the count
- r3: kmctl review due lists the summary with reason `concepts changed: ID, ...` when a concept (manifesto, decision, practice, proposal, prototype README, architecture page) changed in a commit after the last commit that changed the summary, or is changed (or new and untracked) in the working tree while the summary is not; never for log.md, an index, a handoff or the summary itself; a concept changed in the same commit as the summary does not count.
  Fails when: any of these cases is listed wrongly, the reason does not name the changed concepts, or a log, index or handoff change lists it
- r4: An edit to .okf/summary.md, or kmctl summary ack, clears the summary from kmctl review due; ack writes checked.at (today) and checked.against (the concept ids that were listed) into its front matter and nothing else; the summary is never listed as unverified or for stale_after; kmctl check and the CI action report a stale summary without failing.
  Fails when: the summary stays listed after an edit or ack, ack writes anything else, the summary is listed as unverified or stale_after, or kmctl check exits nonzero only because the summary is stale
- r5: checked (checked.at, checked.against) is a named extension field: ALLOWED_FIELDS has its keys, okf.field reads them, and the fields test covers what ack writes; .okf/manifesto.md's I4 names handoff_key and checked.
  Fails when: okf.field raises on checked, the fields test does not cover it, or I4 still says handoff_key is the only extension
- r6: The briefing says Start at .okf/summary.md, and its state line says summary current or summary behind: N concepts changed, within the 500-token budget in the long-handoff-title worst case; the AGENTS.md block kmctl init writes says the same and gives the duty to update the summary or run kmctl summary ack after adding or changing a concept.
  Fails when: the briefing still starts at .okf/index.md, the state line lacks the summary's state, the worst case is over 500 tokens, or the block lacks the pointer or the duty
- r7: This repository has its own .okf/summary.md of at most 500 words linking down to its concepts, and kmctl check passes on it; a decision records the summary, its limit, the freshness rule and ack, and the docs reference lists kmctl summary ack.
  Fails when: the file is missing or over the limit, kmctl check fails, no decision names the summary, or the reference lacks the verb
- r8: The full suite and every tier pass.
  Fails when: any test fails
