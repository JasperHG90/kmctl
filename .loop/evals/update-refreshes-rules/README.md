---
type: eval
title: 'Eval: update-refreshes-rules'
description: 'Definition of done for update-refreshes-rules: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:58:16+00:00'
slug: update-refreshes-rules
signoff:
  signer: human:jasperginn@gmail.com
  hash: 51d14d8a9c93d70c73dfe127b10d3c04309d62656afd5087fbc20f9505c76b85
  at: '2026-10-16T10:58:16+00:00'
verified:
  by: human:jasperginn@gmail.com
  at: '2026-10-16T10:58:16+00:00'
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init replaces an edited copy of a shipped rule with the packaged copy and lists it in updated.
  Fails when: after editing .claude/rules/okf-bundle.md and running init --json, the file differs from src/kmctl/repo_rules/okf-bundle.md or updated does not list it
- r2: A shipped rule that already matches the packaged copy is not rewritten and is listed in skipped.
  Fails when: a second init lists a matching rule anywhere but skipped, or changes its mtime
- r3: init never reads or writes a .claude/rules/ file that is not one of the four shipped rules.
  Fails when: a user rule file in .claude/rules/ changes, or appears in created, updated or skipped
- r4: kmctl update behaves as kmctl init: same options, same --json output, and both are listed in kmctl --help.
  Fails when: kmctl update --json on a fresh repo gives a different JSON object or file tree than kmctl init --json, update rejects --path, or kmctl --help omits update
- r5 (judgment): The help, docs and decision log say init and update replace the four shipped rules, and the new ADR supersedes or corrects ADR 0011's keep-existing-rule clause.
  Fails when: kmctl init --help, docs/reference/commands.md, README.md or the tutorial still says rule files are kept, kmctl update is undocumented, or no decision records the change
