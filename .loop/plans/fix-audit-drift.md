---
type: plan
title: 'Plan: fix-audit-drift'
description: Check each of the 35 mismatches the three DeepSeek audits found on main against the code, and fix the real ones in docs/ and .okf/.
tags:
- plan
slug: fix-audit-drift
epic: null
depends_on: []
priority: null
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:42:52+00:00'
---

# fix-audit-drift

Relayed from: none

## Intent

The three shipped audits (`docs-vs-code`, `okf-vs-code`, `okf-vs-docs`),
run with DeepSeek V4.1 Flash on main at 02c72d80, reported 35 mismatches:
1 high, 17 medium, 17 low. The reports are kept by
spike:fix-audit-drift/1 (its stdout holds all three report.json files). The main threads: the removed `kmctl plugin
install` verb is still described in the manifesto, the architecture page
and ADRs 0001, 0002, 0011, 0015, 0018 and 0020; `.okf/index.md` and the
decision and architecture indexes are stale; the getting-started tutorial
shows `kmctl --version` printing 0.1.0; the explanation page says kmctl has
one hook; the commands reference misses newer kinds, keys and the `docs/`
front matter; and the architecture page still says the audit's default
task is the audit skill.

Each finding is checked against the code before anything changes. A real
mismatch is fixed where it is wrong: a decision gets a `## Correction`
section and never an edit to its body, the manifesto and architecture page
are edited with a `.okf/log.md` line, docs pages are edited, and a
diagram's Depicts section stays true. A finding that does not hold (the
code agrees with the page, or the audit could not check it) is recorded as
such in the fix list, with the line that shows it. The getting-started
tutorial's pasted output is fixed only by running its steps again with the
current kmctl.

Done when the commit message lists every one of the 35 findings as fixed
(with the changed file) or not real (with the evidence), the gates pass,
and a fresh run of the three audits on the result reports none of the
fixed findings again.

## Could invalidate this plan

- none
