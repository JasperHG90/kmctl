---
type: eval
title: 'Eval: adr-audit-fixes'
description: 'Definition of done for adr-audit-fixes: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:50:51+00:00'
slug: adr-audit-fixes
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 378fa5e66c558260a45d57065bd0d0004db196df5dac1d4adc1806f528dc1551
  at: '2026-10-15T12:50:51+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Every front matter key in the repository's own .okf/ is in ALLOWED_FIELDS (I4), so decision_status and decided_on are gone.
  Fails when: any page under .okf/ has a front matter key, nested keys as paths, that ALLOWED_FIELDS lacks
- r2: Every decision record has a Consequences heading, its own or inside an appended Correction section, and the log names every record touched.
  Fails when: a file in .okf/decisions/ other than index.md has no Consequences heading, or .okf/log.md has no line naming one of the nine records
- r3: The briefing names every skill folder the packaged plugin ships (ADR 0002), read at run time.
  Fails when: kmctl briefing's output lacks the name of a folder under the plugin payload's skills/, including a skill folder the test adds to a copy
- r4: The briefing stays inside the I3 word budget, and the bundle passes the okf validator in strict mode.
  Fails when: the existing budget test fails, or okf_validate --strict reports a problem on .okf/
- r5: The supersede module's docstring no longer names decision_status, and supersede still writes only spec fields.
  Fails when: src/kmctl/supersede.py mentions decision_status, or tests/test_supersede.py fails
