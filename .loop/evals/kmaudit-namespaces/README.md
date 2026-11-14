---
type: eval
title: 'Eval: kmaudit-namespaces'
description: 'Definition of done for kmaudit-namespaces: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:07:56+00:00'
slug: kmaudit-namespaces
signoff:
  signer: delegated:jasperginn@gmail.com/claude-main
  hash: e5b62ddfaa83fc99cf47e402d30c4b57212ca976df648be6ac12fa0062e5e219
  at: '2026-11-14T13:07:56+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In a git repository with a plain docs/ folder (no okf_version, no type front matter), `kmaudit claims todo docs --json` hands out a section for every heading of every .md file under docs/, including README.md and nested folders.
  Fails when: the command refuses the folder, exits nonzero, or leaves out a section of any .md file in it
- r2: Claims submitted for the docs namespace are invisible to the .okf namespace and the reverse: `kmaudit claims list` on each shows only its own, and `.kmaudit/` holds one store file per namespace.
  Fails when: a claim from one namespace is listed, counted or handed out under the other, or both namespaces write one file
- r3: A check never reads a file inside the folder it audits: a grep step over ** in the docs namespace matches no file under docs/.
  Fails when: a step's matched files include any path under the audited folder
- r4: `kmaudit namespaces --json` lists each namespace in the repository with its folder and its counts of sections, claims and checks; without --json it prints one line per namespace.
  Fails when: a namespace with a store is missing, its folder or a count is wrong, or the command exits nonzero
- r5: A repository that has only the old .kmctl/audit.sqlite opens the .okf namespace with every row of every table copied, leaves the old file byte for byte unchanged, and hands out no section that was up to date in it.
  Fails when: any table's row count differs between the old file and the .okf namespace's store, the old file changes, or todo hands out a section the old store had extracted at its current key
- r6: The repository root holding .okf/ still means the .okf namespace, so `kmaudit claims todo` with no path, or `.`, works as before.
  Fails when: no path or `.` refuses, or names any namespace but .okf
- r7: instructions_hash() is pinned by a test whose failure message says to empty PREVIOUS_HASHES, so a guidance change cannot carry old answers over unnoticed.
  Fails when: GUIDANCE changes and no test fails, or the failure message does not name PREVIOUS_HASHES
- r8: The review page (`kmaudit ui FOLDER`) and `kmaudit coverage FOLDER` work for a plain folder namespace: the page shows that folder's pages and their claims, and coverage counts code outside it.
  Fails when: the page data for a docs namespace holds no docs page, or coverage counts a file inside the audited folder as code
