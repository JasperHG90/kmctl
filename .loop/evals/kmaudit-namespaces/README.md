---
type: eval
title: 'Eval: kmaudit-namespaces'
description: 'Definition of done for kmaudit-namespaces: 10 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:11:12+00:00'
slug: kmaudit-namespaces
signoff:
  signer: delegated:jasperginn@gmail.com/claude-main
  hash: 74525a5c2c4d6a6ecaef283bb9352b095db4d738327b42ef5187034f51445c6a
  at: '2026-11-14T13:11:12+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In a git repository with a plain docs/ folder (no okf_version, no type front matter), `kmaudit claims todo docs --json` hands out a section for every heading of every .md file under docs/, including README.md and nested folders.
  Fails when: the command refuses the folder, exits nonzero, or leaves out a section of any .md file in it
- r2: Claims submitted with `kmaudit claims submit - --path docs` land in the docs namespace and are invisible to .okf, and the reverse: `kmaudit claims list` on each shows only its own, and `.kmaudit/` holds one store file per namespace; `todo --json` prints its namespace and a next step that spells `--path FOLDER`.
  Fails when: a claim from one namespace is listed, counted or handed out under the other, both namespaces write one file, submit without the right --path stores into another namespace silently, or todo's JSON lacks the namespace or the --path in its next step
- r2b: A path inside an existing namespace narrows it: `kmaudit claims todo docs/sub/page.md` and `kmaudit claims todo docs/sub` mean the docs namespace scoped to those files and open no store of their own; opening a folder that holds an existing namespace is refused on stderr naming that namespace, exit 1.
  Fails when: a subfolder or file of docs opens a second store, scopes to anything but its own files, or opening the parent of an existing namespace succeeds or exits 0
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
- r9: The extract-claims and write-checks agents and skills pass the folder as --path to every kmaudit verb that writes.
  Fails when: an agent or skill names `kmaudit claims submit`, `kmaudit checks try` or `kmaudit checks submit` without --path
