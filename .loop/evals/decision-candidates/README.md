---
type: eval
title: 'Eval: decision-candidates'
description: 'Definition of done for decision-candidates: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T16:02:47+00:00'
slug: decision-candidates
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 4cdf536195b8a70af1ee7fef322c160bb55e81c75bca8e414b0b688a1d07a353
  at: '2026-11-16T16:02:47+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In a temporary git repository, kmctl decision candidates lists one change per ticket merge, per pull request without ticket merges, per ticket inside a pull request that carried tickets and per plain commit, reads through a sync merge, leaves out loop state, release and placeholder commits, and starts by default after the commit that added the newest decision record (or at the root when there is none) or at --since.
  Fails when: a change is missing, listed twice or wrongly split, a skipped commit is listed, or the default or --since start is wrong
- r2: Each listed change carries its sha, first parent, kind, subject, message, ticket slug and plan path when the plan exists, changed files, the decision numbers it added or amended, its signals and score; changes come highest score first; --json prints that list as JSON and the default prints a table; nothing in the repository changes.
  Fails when: a field is missing or wrong, recorded misses an added or amended record, ordering is not by score, the JSON does not parse or lacks a field, or a file or ref changes
- r3: Outside a git repository, or with a --since that names no commit, it exits 1 with one stderr line naming the refusal and the fix; its help names what it produces, gives every input an example and fits 80 columns; docs/reference/commands.md documents it; decision 0047 exists and validates; kmctl check passes.
  Fails when: a refusal exits 0 or lacks the fix, the help tests fail, the reference lacks the verb, or kmctl check or the frontmatter tests report a finding
