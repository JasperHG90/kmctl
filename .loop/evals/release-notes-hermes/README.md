---
type: eval
title: 'Eval: release-notes-hermes'
description: 'Definition of done for release-notes-hermes: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:47:15+00:00'
slug: release-notes-hermes
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 7666d59871b85b7a963199924ff4a2818abff80eefae17a3823ac018a3f54acf
  at: '2026-11-14T17:47:15+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The cleaning script keeps Hermes' rewrite only when it is non-empty, keeps the draft's headings in order, leaves Other changes to the end byte for byte, and keeps exactly the draft's (`slug`) and (#N) references under What changed with one per bullet; otherwise it prints the draft with a ::warning:: naming the failed check, and never exits non-zero.
  Fails when: a rewrite failing any check is kept, a passing one is replaced, the warning does not name the check, or the script exits non-zero
- r2: The Release run's Hermes step uses the pinned action SHA, OLLAMA_API_KEY, deepseek-v4.1-flash and .github/prompts/release-notes-system.md with continue-on-error and a timeout, and the notes file comes from the cleaning script's output.
  Fails when: any of those is missing or differs, or the notes file is written from anything but the cleaning script
