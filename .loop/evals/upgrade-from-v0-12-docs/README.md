---
type: eval
title: 'Eval: upgrade-from-v0-12-docs'
description: 'Definition of done for upgrade-from-v0-12-docs: 1 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T19:47:14+00:00'
slug: upgrade-from-v0-12-docs
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: ad944ae5e3c8faff63ebf9a2cc1575467b11eb7675a7c878d90a721a2bef5002
  at: '2026-11-15T19:47:14+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl's README Upgrade section and the APM how-to tell a v0.12 user, in order, to install the new CLI first, change the apm.yml entry to path packages/kmctl/apm with the new ref (written out in full), run apm install and kmctl plugin patch, and check with kmctl doctor last; they name just upgrade for starter projects; kmctl's README links kmaudit's README for auditing.
  Fails when: either page lacks the CLI-first step, puts doctor before apm install, omits the full new entry or just upgrade, or kmctl's README does not link kmaudit's README
