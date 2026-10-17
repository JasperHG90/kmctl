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
1 high, 17 medium, 17 low. The findings are kept in full by
spike:fix-audit-drift/2 (docs-vs-code, 7), spike:fix-audit-drift/3
(okf-vs-code, 21) and spike:fix-audit-drift/4 (okf-vs-docs, 7); spike 1's
output was cut and is not the input. The main threads: the removed `kmctl plugin
install` verb is still described in the manifesto, the architecture page
and ADRs 0001, 0002, 0011, 0015, 0018 and 0020; `.okf/index.md` and the
decision and architecture indexes are stale; the getting-started tutorial
shows `kmctl --version` printing 0.1.0; the explanation page says kmctl has
one hook; the commands reference misses newer kinds, keys and the `docs/`
front matter; and the architecture page still says the audit's default
task is the audit skill.

Each finding is checked against the code before anything changes. The
scope is `docs/`, `.okf/`, and the CLI help strings in
`src/kmctl/__init__.py` that `docs/reference/commands.md` copies (for
example `review due`'s summary, which still says it lists only `.okf/`
concepts), with the tests that pin them. A real
mismatch is fixed where it is wrong: a decision gets a `## Correction`
section and never an edit to its body, the manifesto and architecture page
are edited with a `.okf/log.md` line, docs pages are edited, and a
diagram's Depicts section stays true. A finding in a decision's front-matter
`description` or its line in `.okf/decisions/index.md` is not reached by a
Correction: the record keeps its description, since a record is never
rewritten (`.claude/rules/okf-bundle.md`), and its index line gets a
short note after the summary, as "(superseded by ADR 00NN)" already does,
naming the Correction or later ADR that changes it. Concept counts in
`.okf/index.md` are dropped rather than updated, since nothing keeps them
true. The "one hook" finding is fixed as wording: kmctl's own hook is still
SessionStart only (ADR 0004), and okf's opt-in Stop check is okf's. A finding that does not hold (the
code agrees with the page, or the audit could not check it) is recorded as
such in the fix list, with the line that shows it. The getting-started
tutorial's pasted output is fixed only by running its steps again with the
current kmctl.

Done when the commit message lists every one of the 35 findings as fixed
(with the changed file) or not real (with the evidence), and the gates
pass. Then the three audits run once more on the result: a finding of the
35 that comes back is checked against the code again and fixed, or
recorded as not real with the evidence; a new finding outside the 35 goes
to a follow-up stub, not this ticket. There is one rerun, not a loop.

## Could invalidate this plan

- none
