---
type: eval
title: 'Eval: new-concept-freshness'
description: 'Definition of done for new-concept-freshness: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T19:03:24+00:00'
slug: new-concept-freshness
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: bc3cbfabdce2940c39f8204eb56b868213224139bcb7bed035aa54b89f842781
  at: '2026-10-15T19:03:24+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl new writes stale_after as a UTC timestamp from a duration (30d, 12w, 6m, 1y) or a date, for every kind, and a handoff's --stale-after replaces its 14-day default.
  Fails when: for any kind or any of those forms the written stale_after is missing or not the expected UTC time, or a handoff given --stale-after still gets the 14-day default
- r2: kmctl new refuses a past date or an unparseable --stale-after with a message naming the value, writing nothing.
  Fails when: a past date or a value like 'soon' or '30x' is accepted, the message does not name the value, or any file is written
- r3: kmctl new writes every --source path, in order, as resource mappings, accepts an existing file git does not track yet, refuses a path that does not exist (naming it) and refuses --source on a handoff; kmctl review due lists the concept as due after a commit that changes a source.
  Fails when: the sources list is missing a path, out of order, or not resource mappings; an existing untracked file is refused; a missing path is accepted or not named; a handoff accepts --source; or after verifying the concept and committing a change to its source, review due does not list it with the source-changed reason
- r4: Front matter written with both options passes the strict okf validator and the I4 written-fields test.
  Fails when: okf_validate --strict fails on a bundle with such concepts, or tests/test_okf_fields.py fails
- r5: The kmctl block's duties tell agents to name the code a concept describes with --source and to give anything time-bound a --stale-after; kmctl new --help and the reference describe both options.
  Fails when: the block written by kmctl init lacks either option, or kmctl new decision --help or docs/reference/commands.md does not describe both
- r6: The other tests still pass.
  Fails when: any test fails
